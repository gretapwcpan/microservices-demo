FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY src/agentic-ai/agents/shopping-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY src/agentic-ai/agents/shopping-agent/agent.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8081

EXPOSE 8081

CMD ["python", "agent.py"]
