# Base image compatible with Python 3.9 and Home Assistant addons
FROM python:3.10-slim

RUN apt update && apt install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy the addon files into the container
COPY app/ /app/
COPY requirements.txt /requirements.txt
COPY server.py /server.py
RUN chmod +x /server.py

# Install Python dependencies
RUN pip install -r requirements.txt

# Entrypoint to start the addon
CMD [ "uvicorn", "server:app", "--port", "8002" ]