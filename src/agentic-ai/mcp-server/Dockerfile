FROM python:3.11-slim

WORKDIR /app

# Copy protobuf definitions from project root
COPY protos/ ./protos/

# Generate gRPC code
RUN python -m pip install grpcio-tools==1.59.3
RUN mkdir -p ./genproto && \
    python -m grpc_tools.protoc -I./protos --python_out=./genproto --grpc_python_out=./genproto ./protos/demo.proto && \
    sed -i 's/import demo_pb2/from . import demo_pb2/g' ./genproto/demo_pb2_grpc.py

# Install dependencies
COPY src/agentic-ai/mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY src/agentic-ai/mcp-server/server.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

EXPOSE 8080

CMD ["python", "server.py"]
