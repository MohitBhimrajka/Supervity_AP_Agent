# Supervity AP Agent: An AI-Powered Accounts Payable Copilot

This project is an advanced, AI-powered Accounts Payable (AP) automation platform. It goes beyond simple data extraction by providing a sophisticated **AP Copilot**, built with Google's Gemini Pro, that allows users to analyze data, manage workflows, and take action using natural language.

The system ingests invoices, purchase orders (POs), and goods receipt notes (GRNs), performs automated 3-way matching, and flags exceptions for review. The AP Copilot then acts as an intelligent assistant for the AP team to resolve these issues, optimize payments, and gain strategic insights.

## 🚀 Key Features

*   **Intelligent Document Processing (IDP):** Ingests PDF documents (Invoices, POs, GRNs) and uses Gemini AI to extract structured data with high accuracy.
*   **Automated 3-Way Matching:** A robust matching engine validates invoices against POs and GRNs, checking for mismatches in price, quantity, items, and more.
*   **Comprehensive Exception Handling:** Automatically flags invoices with issues like price/quantity discrepancies, missing documents, duplicates, and policy violations.
*   **Conversational AI Copilot:** A stateful, tool-augmented agent that understands user intent and can:
    *   **Retrieve Data:** Answer complex questions about invoices, vendors, and system performance.
    *   **Take Action:** Approve/reject invoices, edit POs, and update vendor settings directly from chat.
    *   **Analyze & Forecast:** Provide spending analysis, cash flow forecasts, and anomaly detection.
    *   **Automate Communication:** Draft vendor emails for dispute resolution.
*   **Advanced KPI Dashboard:** Real-time visibility into critical AP metrics, including processing times, touchless rates, and financial optimization opportunities like early payment discounts.
*   **RESTful API:** A clean, well-documented FastAPI backend for seamless integration with any frontend.

## 🤖 The AP Copilot: Your Intelligent Assistant

The heart of the system is the AP Copilot. It's designed to understand the context of AP operations. You can have conversations like this:

**1. Investigate an Issue:**
> **You:** "Show me all invoices that need review."
>
> **Copilot:** "I've found 11 invoices that need review. The data is loaded for you to see."
>
> **You:** "What's the problem with invoice INV-AM-98002?"
>
> **Copilot:** "Invoice INV-AM-98002 has a **Price Mismatch**. The unit price for 'Cutting Disc' is $11.00, but the PO price was $10.00, which is outside the tolerance."

**2. Take Corrective Action:**
> **You:** "Okay, ArcelorMittal's prices are often slightly off. Let's update their price tolerance to 10%."
>
> **Copilot:** "I have updated the price tolerance for ArcelorMittal to 10%."
>
> **You:** "Great. Now approve invoice INV-AM-98002 with the reason 'Price difference within new tolerance'."
>
> **Copilot:** "Invoice INV-AM-98002 has been successfully approved for payment."

**3. Analyze and Forecast:**
> **You:** "Give me a KPI summary."
>
> **You:** "What's our payment forecast for the next 30 days?"
>
> **You:** "Draft an email to the vendor for invoice INV-AM-98003 regarding the quantity mismatch."

**4. Edit and Regenerate Documents:**
> **You:** "Edit PO-78003 and change the ordered quantity of 'Safety Gloves' to 110."
>
> **Copilot:** "Great! The quantity for 'Safety Gloves' on PO-78003 has been successfully updated to 110."
>
> **You:** "Now regenerate the PDF for PO-78003."
>
> **Copilot:** "I have generated a new PDF for PO-78003. You can find it at `generated_documents/REGEN_PO-78003_... .pdf`."

## 📋 Setup and Running the Application

### 1. Prerequisites
*   Python 3.10+
*   A Google Gemini API Key

### 2. Installation
   - **Get your API key:** Get your key from [Google AI Studio](https://makersuite.google.com/app/apikey).
   - **Create a `.env` file** in the project root by copying `.env.example` (if provided) or creating it from scratch.
   - **Add your API key** to the `.env` file:
     ```
     GOOGLE_API_KEY="your_actual_api_key_here"
     ```
   - **Create and activate a virtual environment:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate  # On macOS/Linux
     # venv\Scripts\activate     # On Windows
     ```
   - **Install dependencies:**
     ```bash
     pip install -r requirements.txt
     ```

### 3. Database Setup
   - The application uses SQLite and will create the `ap_data.db` file automatically.
   - To start with a clean slate, you can reset the database at any time:
     ```bash
     python scripts/cleanup_db.py --reset
     ```

### 4. Running the Server

#### Option A: Fresh Start (Recommended for Development)
   - Use the fresh start script to clean the database, initialize config, and run the server:
     ```bash
     python run_fresh.py
     ```
     or
     ```bash
     ./run_fresh.sh
     ```
   - For a complete database reset (drop and recreate tables):
     ```bash
     python run_fresh.py --reset
     ```

#### Option B: Standard Start
   - Execute the run script:
     ```bash
     python run.py
     ```

   - The API will be available at `http://127.0.0.1:8000`.
   - Interactive API documentation (via Swagger UI) is available at `http://127.0.0.1:8000/docs`.

## 🧪 Testing the System (Quickstart)

### Method 1: Using Fresh Start (Recommended)
1.  **Start fresh** (cleans DB, initializes config, and starts server):
    ```bash
    python run_fresh.py
    ```
2.  **Generate sample data:**
    ```bash
    python scripts/data_generator.py
    ```

### Method 2: Manual Setup
1.  **Reset the database** as shown above.
2.  **Generate sample data:**
    ```bash
    python scripts/data_generator.py
    ```
3.  **Start the application** with `python run.py`.

### Next Steps (Both Methods)
4.  **Upload documents:**
    - Go to the API docs at `http://127.0.0.1:8000/docs`.
    - Use the `POST /api/documents/upload` endpoint to upload all the PDF files from the `sample_data/arcelormittal_documents` directory.
5.  **Interact with the Copilot:**
    - Use the `POST /api/copilot/chat` endpoint in the API docs (or a connected frontend) to ask the questions listed in "The AP Copilot" section above.
    - Observe the console logs to see the agent's reasoning and tool usage.

## 🏗️ Project Structure

```
Tungsten_AP_Agent/
├── .env                    # Store your API key here
├── run.py                  # Main startup script
├── requirements.txt
├── README.md               # This file
├── ap_data.db              # SQLite database file
├── sample_data/            # Sample PDFs and PDF generation templates
├── generated_documents/    # Output directory for regenerated PDFs
├── scripts/                # Helper scripts (data generation, db cleanup)
│   ├── data_generator.py
│   └── cleanup_db.py
└── src/app/                # Main application source code
    ├── main.py             # FastAPI app initialization and routing
    ├── config.py           # Application configuration
    ├── api/                # API endpoints
    │   └── endpoints/
    │       ├── copilot.py
    │       ├── dashboard.py
    │       └── invoices.py
    ├── db/                 # Database setup
    │   ├── models.py       # SQLAlchemy ORM models
    │   ├── schemas.py      # Pydantic data validation schemas
    │   └── session.py
    ├── modules/            # Core business logic modules
    │   ├── ingestion/      # Document extraction (IDP)
    │   │   ├── extractor.py
    │   │   └── service.py
    │   ├── matching/       # 3-way matching engine
    │   │   └── engine.py
    │   └── copilot/        # The AI Copilot agent and its tools
    │       ├── agent.py
    │       └── tools.py
    └── utils/              # Shared utilities
```