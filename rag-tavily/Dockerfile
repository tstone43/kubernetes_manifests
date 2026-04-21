FROM python:3.11-slim

ENV TAVILY_API_KEY=""
ENV LLAMA_URL=""

# Install dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy app + static frontend
COPY appv2.py /app/app.py
COPY static /app/static

WORKDIR /app

# Expose FastAPI port
EXPOSE 8000

# Run the server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]