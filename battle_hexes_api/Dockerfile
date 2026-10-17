FROM python:3.12.3-slim-bookworm@sha256:afc139a0a640942491ec481ad8dda10f2c5b753f5c969393b12480155fe15a63 AS ppo-training

# Dockerfile for the battle_hexes_api service

# Set up work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements-ppo-serving.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-ppo-serving.txt

# Copy application source
COPY battle_hexes_core ./battle_hexes_core
COPY battle_agent_rl ./battle_agent_rl
COPY battle_hexes_api ./battle_hexes_api

# Make source packages importable
ENV PYTHONPATH=/app/battle_hexes_core/src:/app/battle_agent_rl/src:/app/battle_hexes_api/src

# Training can use the pinned ARM64 runtime without requiring an old artifact.
FROM ppo-training AS api
ENV BATTLE_HEXES_PPO_RUN_DIR=/app/battle_agent_rl/archive/ppo/arm64
RUN python -c "import os; from battle_agent_rl.ppo.playable_artifact import load_model; load_model(os.environ['BATTLE_HEXES_PPO_RUN_DIR'])"

# Expose API port
WORKDIR /app/battle_hexes_api
EXPOSE 8000

# Start the API using Uvicorn
CMD ["uvicorn","battle_hexes_api.main:app","--host","0.0.0.0","--port","8000","--proxy-headers"]
