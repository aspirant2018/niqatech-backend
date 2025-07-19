# Using an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# instal dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# expose port 8000
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app","--host", "0.0.0.0","--port","8000"]