# Base image compatible with Python 3.9 and Home Assistant addons
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the addon files into the container
COPY app/ /app/
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set permissions for the app directory
RUN chmod +x /app/main.py

# Entrypoint to start the addon
CMD [ "uvicorn", "" ]