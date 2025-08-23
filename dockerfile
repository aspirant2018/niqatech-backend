# Use official Python image
FROM python:3.12-slim

# Set environment variables

ENV GOOGLE_CLIENT_ID=245808035770-5e2rf7c0a5kqcfd6d7q4h9r0car8mttc.apps.googleusercontent.com
ENV SECRET_KEY=1234
ENV ALGORITHM=HS256
ENV OPENAI_API_KEY=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

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the application code
COPY . .

# Expose port (FastAPI default)
EXPOSE 8000

# Command to run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
