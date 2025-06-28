# src/app/modules/copilot/agent.py
import json
from typing import Optional, Dict, Any
from app.config import settings
from app.db.session import SessionLocal
from . import tools
from google import genai
from google.genai import types

# Configure the Gemini client
client = None
try:
    client = genai.Client(api_key=settings.google_api_key)
    print("Copilot GenAI client configured successfully")
except Exception as e:
    print(f"Copilot GenAI client configuration failed, check API key. Error: {e}")

# Define the system prompt and persona
SYSTEM_PROMPT = """You are Supervity, an expert Accounts Payable Co-pilot. Your purpose is to help users analyze data, manage workflows, and take action. You are proactive and insightful.

- **Data Retrieval:** When asked to get data (KPIs, invoices), use the tools, summarize the result, and let the user know details are loaded.
- **Actions:** When asked to perform an action (approve, reject, create proposals, edit), confirm the action you are taking.
- **Single-Action Focus:** You must handle one action at a time. If a user asks you to perform multiple actions in one message (e.g., "Approve invoice A and B"), perform only the first action and politely inform the user that you have completed it and they can now ask for the next one.
- **Analysis & Communication:** When asked to analyze spending, find anomalies, or draft emails, use the provided tools to generate insightful and helpful content.
- **Context:** Maintain context in conversations. If a user finds invoices, they can then act on them in the next message.
- **Clarity:** Be concise. If a tool fails or you lack information, state it clearly. Never make up information.
"""

# Create proper tool definitions for the new SDK
def create_tool_definitions():
    """Create tool definitions for Gemini function calling"""
    return [
        types.Tool(
            function_declarations=[
                # READ-ONLY & ANALYSIS TOOLS
                tools.get_system_kpis_declaration,
                tools.search_invoices_declaration,
                tools.get_invoice_details_declaration,
                tools.summarize_vendor_issues_declaration,
                tools.flag_potential_anomalies_declaration,
                tools.analyze_spending_by_category_declaration,
                tools.get_payment_forecast_declaration,
                tools.get_learned_heuristics_declaration,
                tools.get_notifications_declaration,

                # ACTION & WORKFLOW TOOLS
                tools.approve_invoice_declaration,
                tools.reject_invoice_declaration,
                tools.update_vendor_tolerance_declaration,
                tools.edit_purchase_order_declaration,
                tools.regenerate_po_pdf_declaration,
                tools.create_payment_proposal_declaration,
                tools.draft_vendor_communication_declaration,
                tools.create_automation_rule_declaration,
            ]
        )
    ]

def format_ui_response(text: str, action: str = "DISPLAY_TEXT", data: Any = None) -> Dict[str, Any]:
    """Standardizes the response format for the frontend."""
    return {
        "responseText": text,
        "uiAction": action,
        "data": data,
    }


def invoke_agent(user_message: str, current_invoice_id: Optional[str] = None) -> Dict[str, Any]:
    """
    The main orchestrator for the Copilot using function calling with proper tool handling.
    """
    if not client:
        return format_ui_response("I'm sorry, the AI service is not properly configured. Please check the API key.")
    
    db = SessionLocal()
    try:
        # Prepare the user message with context
        if current_invoice_id:
            context_message = f"(The user is currently viewing invoice: {current_invoice_id}) User question: {user_message}"
        else:
            context_message = user_message
        
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=context_message)])]
        
        gemini_tools = create_tool_definitions()
        
        # Configure generation
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ],
            tools=gemini_tools,
            response_mime_type="text/plain",
        )
        
        # Initial call to Gemini to see if it wants to use a tool
        response_text = ""
        function_calls = None
        
        for chunk in client.models.generate_content_stream(
            model=settings.gemini_model_name,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.function_calls is None:
                if chunk.text:
                    response_text += chunk.text
            else:
                function_calls = chunk.function_calls

        # Check if the model wants to call a function
        if function_calls:
            # Execute the first function call
            function_call = function_calls[0]
            tool_name = function_call.name
            tool_args = dict(function_call.args) if function_call.args else {}

            if tool_name not in tools.AVAILABLE_TOOLS:
                return format_ui_response(f"Error: Unknown tool requested: {tool_name}")

            print(f"Agent wants to call tool '{tool_name}' with args: {tool_args}")
            
            tool_function = tools.AVAILABLE_TOOLS[tool_name]
            # Ensure 'db' is passed to every tool, and 'client' to tools that need it
            tool_args['db'] = db
            if tool_name in ["analyze_spending_by_category", "draft_vendor_communication"]:
                tool_args['client'] = client

            tool_result = tool_function(**tool_args)

            # For the streaming API, we need to format the response differently
            # The model expects the function result as a string representation
            tool_result_str = json.dumps(tool_result, default=str) if isinstance(tool_result, (dict, list)) else str(tool_result)
            
            # Send function result back to get final response
            function_response_contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=context_message)]
                ),
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=f"I need to call the {tool_name} function with arguments: {tool_args}")]
                ),
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=f"Function {tool_name} returned: {tool_result_str}. Please provide a helpful response based on this data.")]
                )
            ]
            
            # Get final response from model
            final_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                ],
                response_mime_type="text/plain",
            )
            
            final_response_text = ""
            for chunk in client.models.generate_content_stream(
                model=settings.gemini_model_name,
                contents=function_response_contents,
                config=final_config,
            ):
                if chunk.text:
                    final_response_text += chunk.text
            
            # Determine the UI action based on the tool used
            ui_action = "LOAD_DATA" 
            if tool_name == "get_invoice_details":
                ui_action = "LOAD_SINGLE_DOSSIER"
            elif tool_name in ["get_system_kpis", "summarize_vendor_issues", "regenerate_po_pdf", "get_payment_forecast", "flag_potential_anomalies", "analyze_spending_by_category", "create_payment_proposal"]:
                ui_action = "DISPLAY_JSON"
            elif tool_name in ["draft_vendor_communication"]:
                ui_action = "DISPLAY_MARKDOWN"
            elif tool_name in ["approve_invoice", "reject_invoice", "update_vendor_tolerance", "edit_purchase_order", "create_automation_rule"]:
                ui_action = "SHOW_TOAST_SUCCESS" # A success message for actions

            return format_ui_response(
                text=final_response_text,
                action=ui_action,
                data=tool_result
            )
        else:
            # No function call needed, return direct response
            return format_ui_response(response_text)

    except Exception as e:
        print(f"An error occurred in the Copilot agent: {e}")
        import traceback
        traceback.print_exc()
        return format_ui_response("I'm sorry, I encountered an error. Please try again or rephrase your question.")
    finally:
        db.close() 