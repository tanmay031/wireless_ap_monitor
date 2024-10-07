# app_a/Dockerfile
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the Python script and JSON file into the container
COPY * /app/


# Install necessary Python package
RUN pip install pika

# Run the application
CMD ["python3", "app_a.py"]
