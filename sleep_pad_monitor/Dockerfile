# Base image compatible with Python 3.9 and Home Assistant addons
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the addon files into the container
COPY app/ /app/
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set permissions for the app directory
RUN chmod +x /app/device.py

# Ensure serial devices are accessible
ENV UDEV=1

# Entrypoint to start the addon
CMD [ "python", "/app/device.py" ]