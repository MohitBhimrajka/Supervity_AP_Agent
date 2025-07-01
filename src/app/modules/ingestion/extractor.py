# src/app/modules/ingestion/extractor.py
import json
from typing import Optional, Dict

from google import genai
from google.genai import types

from app.config import settings

# Configure the Gemini client
client = None
try:
    # Use the unified key from settings
    client = genai.Client(api_key=settings.gemini_api_key)
    print("Ingestion GenAI client configured successfully")
except Exception as e:
    print(f"Ingestion GenAI client configuration failed, check API key. Error: {e}")

EXTRACTION_PROMPT = """You are an elite Accounts Payable data extraction engine. Your task is to analyze the attached document with extreme precision and return ONLY a single, minified JSON object. Adhere to these critical rules:

**Your Process:**
1.  **Identify Document Type:** First, classify the document as one of: "Purchase Order", "Goods Receipt Note", "Invoice", or "Error".
2.  **Extract Data:** Based on the type, extract all available fields according to the corresponding schema below.
3.  **Strict Data Typing:** Before outputting the JSON, double-check your work.
    -   **Dates MUST be in "YYYY-MM-DD" format.** (e.g., "2024-03-15").
    -   **Numbers MUST be pure numeric types (integer or float), not strings.** (e.g., 1800.00, not "$1,800.00" or "1,800").
    -   Use `null` for any field you cannot find.
4.  **Output JSON:** Provide only the final JSON object. Do not include any other text, explanations, or markdown formatting.

**JSON Schemas:**

**1. If Purchase Order:**
{"document_type": "Purchase Order", "po_number": "string", "vendor_name": "string", "buyer_name": "string", "order_date": "YYYY-MM-DD", "line_items": [{"description": "string", "ordered_qty": float, "unit_price": float, "sku": "string | null", "unit": "string | null"}], "subtotal": float | null, "tax": float | null, "grand_total": float | null}

**2. If Goods Receipt Note:**
{"document_type": "Goods Receipt Note", "grn_number": "string", "po_number": "string", "received_date": "YYYY-MM-DD", "line_items": [{"description": "string", "received_qty": float, "sku": "string | null", "unit": "string | null"}]}

**3. If Vendor Invoice:**
{"document_type": "Invoice", "invoice_id": "string", "vendor_name": "string", "related_po_numbers": ["string"], "related_grn_numbers": ["string"], "invoice_date": "YYYY-MM-DD", "due_date": "YYYY-MM-DD", "line_items": [{"description": "string", "quantity": float, "unit_price": float, "line_total": float, "sku": "string | null", "po_number": "string | null", "unit": "string | null"}], "subtotal": float | null, "tax": float | null, "grand_total": float | null, "discount_terms": "string | null", "discount_amount": float | null, "discount_due_date": "YYYY-MM-DD | null"}

**4. If Unreadable or Not an AP Document:**
{"document_type": "Error", "error_message": "The document is illegible, password-protected, or not a recognizable AP document type."}"""

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