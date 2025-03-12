# Deployment Guide for APIFromAnything

This guide provides instructions for deploying APIs built with the APIFromAnything library in various environments.

## Table of Contents

- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Serverless Deployment](#serverless-deployment)
  - [AWS Lambda](#aws-lambda)
  - [Google Cloud Functions](#google-cloud-functions)
  - [Azure Functions](#azure-functions)
- [Traditional Server Deployment](#traditional-server-deployment)
  - [Gunicorn + Nginx](#gunicorn--nginx)
  - [uWSGI + Nginx](#uwsgi--nginx)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Monitoring and Observability](#monitoring-and-observability)
- [Security Considerations](#security-considerations)

## Local Development

For local development, you can run your API directly using the built-in server:

```python
from apifrom import API, api

app = API(
    title="My API",
    description="My API description",
    version="1.0.0"
)

@api(route="/hello", method="GET")
def hello() -> dict:
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
```

This is suitable for development but not recommended for production use.

## Docker Deployment

### Dockerfile

Create a `Dockerfile` in your project root:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

### Docker Compose

For more complex setups, you can use Docker Compose. Create a `docker-compose.yml` file:

```yaml
version: '3'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    restart: always
```

### Building and Running

```bash
# Build the Docker image
docker build -t my-api .

# Run the container
docker run -p 8000:8000 my-api

# Or using Docker Compose
docker-compose up
```

## Serverless Deployment

### AWS Lambda

To deploy your APIFromAnything API to AWS Lambda, you'll need to create an adapter for AWS Lambda events.

#### Installation

```bash
pip install mangum
```

#### Lambda Handler

Create a file named `lambda_handler.py`:

```python
from mangum import Mangum
from your_api_module import app  # Import your API instance

# Create the handler
handler = Mangum(app)
```

#### Serverless Framework Configuration

If you're using the Serverless Framework, create a `serverless.yml` file:

```yaml
service: apifrom-api

provider:
  name: aws
  runtime: python3.9
  region: us-east-1
  memorySize: 256
  timeout: 30

functions:
  api:
    handler: lambda_handler.handler
    events:
      - http:
          path: /{proxy+}
          method: any
```

### Google Cloud Functions

For Google Cloud Functions, create a `main.py` file:

```python
from functions_framework import http
from your_api_module import app  # Import your API instance

@http
def entry_point(request):
    # Convert the Flask request to a raw ASGI scope
    return app(request)
```

### Azure Functions

For Azure Functions, create a `function_app.py` file:

```python
import azure.functions as func
from your_api_module import app  # Import your API instance

async def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    # Convert the request to an ASGI scope
    return await app(req, context)
```

## Traditional Server Deployment

### Gunicorn + Nginx

#### Gunicorn Configuration

Create a file named `gunicorn_config.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
```

#### Nginx Configuration

Create a file named `nginx.conf`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Running with Gunicorn

```bash
gunicorn -c gunicorn_config.py your_api_module:app
```

### uWSGI + Nginx

#### uWSGI Configuration

Create a file named `uwsgi.ini`:

```ini
[uwsgi]
http = 127.0.0.1:8000
module = your_api_module:app
processes = 4
threads = 2
```

#### Running with uWSGI

```bash
uwsgi --ini uwsgi.ini
```

## Kubernetes Deployment

### Kubernetes Deployment YAML

Create a file named `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apifrom-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: apifrom-api
  template:
    metadata:
      labels:
        app: apifrom-api
    spec:
      containers:
      - name: api
        image: your-registry/apifrom-api:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
          requests:
            cpu: "0.5"
            memory: "256Mi"
        env:
        - name: ENVIRONMENT
          value: production
```

### Kubernetes Service YAML

Create a file named `service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: apifrom-api
spec:
  selector:
    app: apifrom-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Deploying to Kubernetes

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Monitoring and Observability

### Prometheus Integration

To integrate with Prometheus for metrics collection, you can use the `prometheus_client` library:

```python
from prometheus_client import Counter, Histogram
import time
from apifrom import API, api
from apifrom.middleware import BaseMiddleware

# Create metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])

# Create a middleware for metrics
class PrometheusMiddleware(BaseMiddleware):
    async def process_request(self, request, next_middleware):
        start_time = time.time()
        
        try:
            response = await next_middleware(request)
            status = response.status_code
        except Exception as e:
            status = 500
            raise e
        finally:
            duration = time.time() - start_time
            REQUEST_COUNT.labels(request.method, request.path, status).inc()
            REQUEST_LATENCY.labels(request.method, request.path).observe(duration)
        
        return response

# Add the middleware to your API
app = API(title="My API", description="My API with metrics", version="1.0.0")
app.add_middleware(PrometheusMiddleware())

# Add a metrics endpoint
@api(route="/metrics", method="GET")
def metrics():
    from prometheus_client import generate_latest
    return generate_latest()
```

### Logging Integration

For structured logging, you can use the `structlog` library:

```python
import structlog
from apifrom.plugins import LoggingPlugin

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Create a logging plugin
logging_plugin = LoggingPlugin(logger=logger)

# Add the plugin to your API
app.plugin_manager.register(logging_plugin)
```

## Security Considerations

### HTTPS

Always use HTTPS in production. When deploying behind a reverse proxy like Nginx, configure SSL termination:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Environment Variables

Store sensitive information like API keys, database credentials, and JWT secrets in environment variables:

```python
import os
from apifrom import API, api
from apifrom.security import jwt_required

# Get secrets from environment variables
JWT_SECRET = os.environ.get("JWT_SECRET")
DB_CONNECTION = os.environ.get("DB_CONNECTION")

app = API(title="Secure API", description="API with secure configuration", version="1.0.0")

@api(route="/protected", method="GET")
@jwt_required(secret=JWT_SECRET)
def protected_endpoint(request):
    return {"message": "This endpoint is protected"}
```

### Rate Limiting

Configure rate limiting to prevent abuse:

```python
from apifrom import API
from apifrom.middleware import RateLimitMiddleware, FixedWindowRateLimiter

app = API(title="Rate Limited API", description="API with rate limiting", version="1.0.0")

# Add rate limiting middleware
rate_limiter = FixedWindowRateLimiter(limit=100, window=60)  # 100 requests per minute
app.add_middleware(RateLimitMiddleware(limiter=rate_limiter))
```

### Security Headers

Add security headers to your responses:

```python
from apifrom import API
from apifrom.middleware import BaseMiddleware

class SecurityHeadersMiddleware(BaseMiddleware):
    async def process_request(self, request, next_middleware):
        response = await next_middleware(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

app = API(title="Secure API", description="API with security headers", version="1.0.0")
app.add_middleware(SecurityHeadersMiddleware())
```

This deployment guide should help you deploy your APIFromAnything APIs in various environments with best practices for security, monitoring, and scalability. 