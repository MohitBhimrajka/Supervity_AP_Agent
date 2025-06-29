# src/app/main.py
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import create_db_and_tables, SessionLocal
# --- ADD COPILOT TO IMPORTS ---
from app.api.endpoints import documents, dashboard, invoices, copilot, learning, notifications, configuration, collaboration, payments
from app.core.monitoring_service import run_monitoring_cycle
from app.modules.automation import executor as automation_executor

# --- NEW LIFESPAN MANAGER ---
async def recurring_background_tasks():
    """Wrapper to run all recurring services on a schedule."""
    while True:
        try:
            print("--- Kicking off recurring background tasks ---")
            # Use consistent session management for both services
            with SessionLocal() as db:
                # Proactive Monitoring (runs every hour)
                run_monitoring_cycle(db)
                
                # Automation Engine (runs every 5 minutes)
                automation_executor.run_automation_engine(db)

        except Exception as e:
            print(f"Error in recurring task: {e}")
        # Let's run this more frequently, e.g., every 5 minutes (300 seconds)
        await asyncio.sleep(300)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    print("🚀 Application starting up...")
    create_db_and_tables()
    # Start the background tasks
    task = asyncio.create_task(recurring_background_tasks())
    yield
    # On shutdown
    print("👋 Application shutting down...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Background tasks successfully cancelled.")

# --- MODIFIED APP INITIALIZATION ---
app = FastAPI(
    title="Supervity AP Agent API", # <-- RENAMED
    description="API for an AI-powered Accounts Payable processing system.",
    version="4.2.0", # Version bump
    lifespan=lifespan # Use the new lifespan manager
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Adjust for your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(documents.router, prefix="/api/documents", tags=["Documents & Jobs"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["Invoices"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
# --- INCLUDE THE NEW COPILOT ROUTER ---
app.include_router(copilot.router, prefix="/api/copilot", tags=["Copilot"])
# --- NEW LEARNING ROUTER ---
app.include_router(learning.router, prefix="/api/learning", tags=["Learning & Heuristics"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
# --- NEW CONFIGURATION ROUTER ---
app.include_router(configuration.router, prefix="/api/config", tags=["Configuration"])
# ADD THIS LINE
app.include_router(collaboration.router, prefix="/api", tags=["Collaboration"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])


@app.get("/api/health", tags=["Health Check"])
def health_check():
    return {"status": "ok"} 