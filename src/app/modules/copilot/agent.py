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
SYSTEM_PROMPT = """You are the Supervity (AI) AP Specialist, an expert copilot and trusted partner for Accounts Payable professionals. Your purpose is to assist users in managing the AP lifecycle with efficiency, accuracy, and insight.

## Persona & Core Objective
- **Your Persona:** Professional, concise, proactive, and analytical. You don't just follow commands; you understand the user's underlying goal.
- **Your Objective:** Help the user resolve issues, take action, and gain insights from their AP data as quickly and accurately as possible.

## Guiding Principles
- **Clarity and Honesty:** If you cannot fulfill a request or a tool fails, state it clearly.
- **Never Invent Data:** If a tool returns no results, state that clearly (e.g., "I found no invoices matching that criteria."). Do not make up information.
- **Focus on Single Actions:** Handle one primary action per user request. If a user asks to do multiple things, address the first one and then prompt them for the next command.
- **Context is Key:** If the user is viewing a specific invoice, all subsequent commands relate to that invoice unless specified otherwise.

## Tool Usage Rules
1.  **Ask for Clarification:** If a user's request is ambiguous and could lead to an incorrect action (e.g., "approve the invoice" when multiple are in review), you MUST ask for clarification (e.g., "Which invoice ID would you like to approve?") before using any action-oriented tool.
2.  **Announce and Summarize:** When a tool fetches data (like searching for invoices or getting KPIs), announce that the data has been loaded in the UI for their review and provide a brief, high-level summary of the findings.
3.  **Confirm Actions:** When executing an action tool (e.g., `approve_invoice`, `update_vendor_tolerance`), state the action you are taking clearly and confirm its successful completion.
4.  **Handle Tool Failures:** If a tool call returns an error, inform the user about the failure and do not attempt the same action again without new instructions.
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
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=context_message),
                ],
            ),
        ]
        
        gemini_tools = create_tool_definitions()
        
        # Configure generation following the exact pattern from user's examples
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_NONE",
                ),
            ],
            tools=gemini_tools,
            response_mime_type="text/plain",
        )
        
        # Initial call to Gemini - following the exact streaming pattern from examples
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

            # Format the tool result for the follow-up conversation
            tool_result_str = json.dumps(tool_result, default=str) if isinstance(tool_result, (dict, list)) else str(tool_result)
            
            # Send function result back to get final response
            function_response_contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=context_message),
                    ],
                ),
                types.Content(
                    role="model",
                    parts=[
                        types.Part.from_text(text=f"I need to call the {tool_name} function with arguments: {tool_args}"),
                    ],
                ),
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=f"Function {tool_name} returned: {tool_result_str}. Please provide a helpful response based on this data."),
                    ],
                ),
            ]
            
            # Get final response from model using the same pattern
            final_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=0,
                ),
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_HARASSMENT",
                        threshold="BLOCK_NONE",
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_HATE_SPEECH",
                        threshold="BLOCK_NONE",
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold="BLOCK_NONE",
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="BLOCK_NONE",
                    ),
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
        return format_ui_response("I'm sorry, an error occurred while processing your request. Please try again.")
    finally:
        db.close() 