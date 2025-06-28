# src/app/modules/ingestion/extractor.py
import json
from typing import Optional, Dict

from google import genai
from google.genai import types

from app.config import settings

# Configure the Gemini client
client = None
try:
    client = genai.Client(api_key=settings.google_api_key)
    print("Ingestion GenAI client configured successfully")
except Exception as e:
    print(f"Ingestion GenAI client configuration failed, check API key. Error: {e}")

EXTRACTION_PROMPT = """You are an expert Accounts Payable data entry specialist. Analyze the attached PDF document. First, identify the document type from the following options: Purchase Order, Goods Receipt Note, Vendor Invoice.

Based on the identified type, extract all key information and return it ONLY as a single, minified JSON object. Do not include any other text, explanations, or markdown. Use `null` for any fields you cannot find. Dates must be in YYYY-MM-DD format.

Your JSON output MUST conform to one of the following schemas:

1. If Purchase Order:
{"document_type": "Purchase Order", "po_number": "string", "vendor_name": "string", "buyer_name": "string", "order_date": "YYYY-MM-DD", "line_items": [{"description": "string", "ordered_qty": float, "unit_price": float, "sku": "string | null"}]}

2. If Goods Receipt Note:
{"document_type": "Goods Receipt Note", "grn_number": "string", "po_number": "string", "received_date": "YYYY-MM-DD", "line_items": [{"description": "string", "received_qty": float, "sku": "string | null"}]}

3. If Vendor Invoice:
{"document_type": "Invoice", "invoice_id": "string", "vendor_name": "string", "po_number": "string | null", "grn_number": "string | null", "invoice_date": "YYYY-MM-DD", "due_date": "YYYY-MM-DD", "line_items": [{"description": "string", "quantity": float, "unit_price": float, "line_total": float, "sku": "string | null"}], "subtotal": float, "tax": float, "grand_total": float, "discount_terms": "string | null", "discount_amount": float | null, "discount_due_date": "YYYY-MM-DD | null"}"""

def extract_data_from_pdf(pdf_content: bytes) -> Optional[Dict]:
    """
    Sends PDF content to Gemini and gets structured JSON data back.
    """
    if not client:
        print("Extractor: GenAI client not available. Cannot process PDF.")
        return None

    try:
        # Create content for the request
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=EXTRACTION_PROMPT),
                    types.Part.from_bytes(data=pdf_content, mime_type="application/pdf")
                ]
            )
        ]
        
        # Configure for JSON output
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ],
            response_mime_type="application/json",
        )
        
        # Generate content with streaming
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=settings.gemini_model_name,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                response_text += chunk.text
        
        # Parse the JSON response
        data = json.loads(response_text)
        doc_type = data.get('document_type', 'Unknown')
        doc_id = data.get('invoice_id') or data.get('grn_number') or data.get('po_number')
        print(f"Successfully extracted data for {doc_type}: {doc_id}")
        return data

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response from Gemini: {e}")
        print(f"Raw response: {response_text[:500]}...")
        return None
    except Exception as e:
        print(f"Error processing PDF with Gemini: {e}")
        return None 