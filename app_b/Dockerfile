# app_b/Dockerfile
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the Python script into the container
COPY app_b.py /app/app_b.py

# Install necessary Python package
RUN pip install pika

# Run the application
CMD ["python3", "app_b.py"]
