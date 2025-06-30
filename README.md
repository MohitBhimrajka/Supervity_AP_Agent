# Supervity AP Command Center: An AI-Powered Accounts Payable Platform

This project is an advanced, AI-powered Accounts Payable (AP) automation platform. It goes beyond simple data extraction by providing a sophisticated **AP Copilot**, built with Google's Gemini, that allows users to analyze data, manage workflows, and take action using natural language.

The system ingests invoices, purchase orders (POs), and goods receipt notes (GRNs), performs automated 3-way matching, and flags exceptions for review in the **Resolution Workbench**. The AP Copilot then acts as an intelligent assistant for the AP team to resolve these issues, optimize payments, and gain strategic insights.

## 🚀 Key Features

*   **Intelligent Document Processing (IDP):** Ingests PDF documents (Invoices, POs, GRNs) and uses Gemini AI to extract structured data with high accuracy.
*   **Automated 3-Way Matching:** A robust matching engine validates invoices against POs and GRNs, checking for mismatches in price, quantity, items, and more.
*   **Comprehensive Exception Handling:** Automatically flags invoices with issues like price/quantity discrepancies, missing documents, duplicates, and policy violations.
*   **Conversational AI Copilot:** A stateful, tool-augmented agent that understands user intent and can resolve issues, take actions, and analyze data.
*   **Adaptive Learning:** The system learns from user actions to create heuristics, which can be promoted into permanent automation rules.
*   **Modern Web Interface:** A responsive Next.js frontend with a dashboard, resolution workbench, and configuration settings.
*   **RESTful API:** A clean, well-documented FastAPI backend for seamless integration.

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
*   Node.js and npm (or yarn/pnpm)
*   A Google Gemini API Key

### 2. Backend Setup
   - **Get your API key:** Get your key from [Google AI Studio](https://makersuite.google.com/app/apikey).
   - **Create a `.env` file** in the project root (`Supervity_AP_Agent/`) and add your API key:
     ```
     GEMINI_API_KEY="your_actual_api_key_here"
     ```
   - **Create and activate a virtual environment:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate  # On macOS/Linux
     # venv\Scripts\activate     # On Windows
     ```
   - **Install Python dependencies:**
     ```bash
     pip install -r requirements.txt
     ```

### 3. Frontend Setup
   - **Navigate to the frontend directory:**
     ```bash
     cd supervity-ap-frontend
     ```
   - **Install Node.js dependencies:**
     ```bash
     npm install
     ```
   - **Return to the root directory:**
     ```bash
     cd ..
     ```

### 4. Running the Application

#### Option A: Fresh Start (Recommended)
   - Use the fresh start script to clean the database, initialize config, and run the server:
     ```bash
     # From the root directory (Supervity_AP_Agent/)
     python run_fresh.py
     ```
   - **In a separate terminal**, start the frontend:
     ```bash
     cd supervity-ap-frontend
     npm run dev
     ```

#### Option B: Standard Start
   - **Start the backend:**
     ```bash
     # From the root directory
     python run.py
     ```
   - **In a separate terminal**, start the frontend:
     ```bash
     cd supervity-ap-frontend
     npm run dev
     ```

   - The frontend will be available at `http://localhost:3000`.
   - The backend API docs will be at `http://127.0.0.1:8000/docs`.


## 🧪 Testing the System (Quickstart)

1.  **Start fresh** using `python run_fresh.py` as described above.
2.  **Generate sample data:**
    ```bash
    # From the root directory
    python scripts/data_generator.py
    ```
    This will create PDF documents in the `sample_data/arcelormittal_documents/` directory.
3.  **Start the frontend** (`npm run dev`) if you haven't already.
4.  **Upload documents:**
    -   Navigate to the **Data Center** page at `http://localhost:3000/data-center`.
    -   Click the upload box and select all the PDF files from `sample_data/arcelormittal_documents/`.
    -   Click "Process Documents" and observe the job progress.
5.  **Review and Resolve:**
    -   Once the job is complete, go to the **Resolution Workbench** at `http://localhost:3000/resolution-workbench`.
    -   Select invoices from the queue to view exceptions, compare line items, and approve/reject them.
6.  **Interact with the Copilot:**
    -   Click the "Ask Copilot" button in the header.
    -   Try prompts like: *"Show me a KPI summary"*, *"What's the problem with invoice INV-AM-98002?"*, *"Draft an email for the quantity mismatch on INV-AM-98003."*

## 🏗️ Project Structure

```
Supervity_AP_Agent/
├── run_fresh.py                # Recommended startup script
├── run.py                      # Standard startup script
├── requirements.txt
├── README.md
├── ap_data.db                  # SQLite database file
├── sample_data/                # Sample PDFs and PDF generation templates
├── generated_documents/        # Output for regenerated PDFs
├── scripts/                    # Helper scripts (data generation, db cleanup)
│   └── ...
├── src/app/                    # FastAPI backend source code
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py
│   ├── api/                    # API endpoints
│   ├── db/                     # Database models and session
│   ├── modules/                # Core business logic (Ingestion, Matching, Copilot)
│   └── ...
└── supervity-ap-frontend/      # Next.js frontend application
    ├── public/
    ├── src/
    │   ├── app/                # Next.js App Router (Pages)
    │   ├── components/         # Reusable React components
    │   └── lib/                # API client, context, utils
    └── ...
```