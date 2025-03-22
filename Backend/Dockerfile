# Use official Python slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy code into container
COPY app.py /app/

# Install dependencies directly (no requirements.txt)
RUN pip install --no-cache-dir fastapi uvicorn pydantic

# Expose the port FastAPI runs on
EXPOSE 8000

# Start FastAPI using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]