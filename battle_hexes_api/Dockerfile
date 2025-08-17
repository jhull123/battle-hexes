FROM python:3.11-slim

# Dockerfile for the battle_hexes_api service

# Set up work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY battle_hexes_core ./battle_hexes_core
COPY battle_agent_rl ./battle_agent_rl
COPY battle_hexes_api ./battle_hexes_api

# Make source packages importable
ENV PYTHONPATH=/app/battle_hexes_core/src:/app/battle_agent_rl/src:/app/battle_hexes_api/src

# Expose API port
WORKDIR /app/battle_hexes_api
EXPOSE 8000

# Start the API using Uvicorn
CMD ["uvicorn","battle_hexes_api.main:app","--host","0.0.0.0","--port","8000","--proxy-headers"]
