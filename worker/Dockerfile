FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY worker.py .

# Environment variables
ENV COMFY_URL=http://comfyui:8188
ENV DATABASE_URL=postgresql://comfyui:comfyui123@postgres:5432/comfyui

# Run worker
CMD ["python", "worker.py"]
