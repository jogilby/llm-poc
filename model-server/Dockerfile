# Start from the official Python image
FROM python:3.9-slim

# Install any system dependencies needed
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code and modules
COPY vectorization/ /app/vectorization/
COPY inferencing/ /app/inferencing/
COPY app.py .

# Expose port 80
EXPOSE 80

# Environment variable to specify model name (optional)
ENV MODEL_NAME=distilgpt2

# Command to run our Flask server
CMD ["python", "app.py"]