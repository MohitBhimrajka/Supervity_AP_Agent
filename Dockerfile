# Stage 1: Build with dependencies
FROM python:3.11-slim as builder

WORKDIR /opt/venv

# Install build essentials required for some python packages
RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .
RUN python -m venv .
RUN . bin/activate && pip install --no-cache-dir -r requirements.txt

# Stage 2: Final production image
FROM python:3.11-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy all necessary application code and data
COPY src ./src
COPY scripts ./scripts
COPY sample_data ./sample_data
COPY generated_documents ./generated_documents
COPY run.py .
COPY run_fresh.py .
COPY requirements.txt .

# Add the venv to the PATH
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8000

# Set the command to run the application.
# `run_fresh.py` initializes the database and then starts the server.
# The `run.py` script has been updated to bind to 0.0.0.0 in production.
CMD ["python", "run_fresh.py"] 