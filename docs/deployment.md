# Deployment Guide for APIFromAnything

This guide provides instructions for deploying APIs built with APIFromAnything in various environments, including Docker, Kubernetes, and serverless platforms.

## Table of Contents

- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Serverless Deployment](#serverless-deployment)
- [AWS Lambda](#aws-lambda)
- [Google Cloud Functions](#google-cloud-functions)
- [Azure Functions](#azure-functions)
- [Performance Considerations](#performance-considerations)
- [Monitoring in Production](#monitoring-in-production)

## Docker Deployment {#docker-deployment}

Docker provides a consistent and isolated environment for running your API. Here's how to containerize an API built with APIFromAnything:

### 1. Create a Dockerfile

Create a `Dockerfile` in your project root:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port your API will run on
EXPOSE 8000

# Command to run the API
CMD ["python", "app.py"]
```

### 2. Create a requirements.txt file

Make sure your `requirements.txt` includes APIFromAnything and any other dependencies:

```
apifrom>=0.1.0
```

### 3. Build the Docker image

```bash
docker build -t my-api .
```

### 4. Run the Docker container

```bash
docker run -p 8000:8000 my-api
```

### 5. Docker Compose (Optional)

For more complex setups with multiple services, create a `docker-compose.yml` file:

```yaml
version: '3'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    restart: always
    
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    depends_on:
      - api
```

Run with:

```bash
docker-compose up
```

## Kubernetes Deployment {#kubernetes-deployment}

Kubernetes provides a robust platform for deploying, scaling, and managing containerized applications.

### 1. Create a Kubernetes Deployment

Create a file named `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-api
  labels:
    app: my-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-api
  template:
    metadata:
      labels:
        app: my-api
    spec:
      containers:
      - name: my-api
        image: my-api:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "100m"
            memory: "256Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 2. Create a Kubernetes Service

Create a file named `service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-api-service
spec:
  selector:
    app: my-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. Apply the Kubernetes configurations

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### 4. Horizontal Pod Autoscaling (Optional)

Create a file named `hpa.yaml`:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

Apply the HPA configuration:

```bash
kubectl apply -f hpa.yaml
```

## Serverless Deployment {#serverless-deployment}

APIFromAnything can be deployed to serverless platforms, allowing you to run your API without managing servers.

### AWS Lambda {#aws-lambda}

#### 1. Create a Lambda handler

Create a file named `lambda_handler.py`:

```python
from apifrom.core.app import APIApp
from apifrom.decorators.api import api
from apifrom.adapters.aws_lambda import LambdaAdapter

# Create an API application
app = APIApp(title="My Serverless API")

# Define API endpoints
@api(app)
def hello(name: str = "World") -> dict:
    """Say hello to someone."""
    return {"message": f"Hello, {name}!"}

# Create a Lambda adapter
lambda_adapter = LambdaAdapter(app)

# Lambda handler function
def handler(event, context):
    """AWS Lambda handler function."""
    return lambda_adapter.handle(event, context)
```

#### 2. Package your application

Create a deployment package by installing dependencies in a local directory and zipping everything:

```bash
pip install apifrom -t ./package
cp lambda_handler.py ./package/
cd package
zip -r ../deployment.zip .
```

#### 3. Deploy to AWS Lambda

Using the AWS CLI:

```bash
aws lambda create-function \
  --function-name my-api \
  --runtime python3.9 \
  --handler lambda_handler.handler \
  --zip-file fileb://deployment.zip \
  --role arn:aws:iam::123456789012:role/lambda-execution-role
```

#### 4. Configure API Gateway

1. Create a new REST API in API Gateway
2. Create a resource and method that integrates with your Lambda function
3. Deploy the API to a stage

### Google Cloud Functions {#google-cloud-functions}

#### 1. Create a Cloud Function handler

Create a file named `main.py`:

```python
from apifrom.core.app import APIApp
from apifrom.decorators.api import api
from apifrom.adapters.gcp_functions import CloudFunctionAdapter

# Create an API application
app = APIApp(title="My Serverless API")

# Define API endpoints
@api(app)
def hello(name: str = "World") -> dict:
    """Say hello to someone."""
    return {"message": f"Hello, {name}!"}

# Create a Cloud Function adapter
cf_adapter = CloudFunctionAdapter(app)

# Cloud Function handler
def handler(request):
    """Google Cloud Function handler."""
    return cf_adapter.handle(request)
```

#### 2. Create a requirements.txt file

```
apifrom>=0.1.0
```

#### 3. Deploy to Google Cloud Functions

Using the gcloud CLI:

```bash
gcloud functions deploy my-api \
  --runtime python39 \
  --trigger-http \
  --entry-point handler
```

### Azure Functions {#azure-functions}

#### 1. Create an Azure Function project

Initialize an Azure Functions project:

```bash
func init my-api-project --python
cd my-api-project
func new --name my-api --template "HTTP trigger"
```

#### 2. Modify the function code

Edit `my-api/__init__.py`:

```python
import azure.functions as func
from apifrom.core.app import APIApp
from apifrom.decorators.api import api
from apifrom.adapters.azure_functions import AzureFunctionAdapter

# Create an API application
app = APIApp(title="My Serverless API")

# Define API endpoints
@api(app)
def hello(name: str = "World") -> dict:
    """Say hello to someone."""
    return {"message": f"Hello, {name}!"}

# Create an Azure Function adapter
azure_adapter = AzureFunctionAdapter(app)

# Azure Function handler
def main(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function handler."""
    return azure_adapter.handle(req)
```

#### 3. Update requirements.txt

```
azure-functions
apifrom>=0.1.0
```

#### 4. Deploy to Azure Functions

```bash
func azure functionapp publish my-api-app
```

## Performance Considerations {#performance-considerations}

When deploying APIFromAnything in production, consider the following performance optimizations:

### 1. Asynchronous Processing

Use asynchronous endpoints for I/O-bound operations:

```python
@api(app)
async def fetch_data() -> dict:
    """Fetch data asynchronously."""
    # Asynchronous I/O operations
    result = await some_async_operation()
    return {"data": result}
```

### 2. Caching

Implement caching for frequently accessed endpoints:

```python
from apifrom.middleware.cache import cache

@api(app)
@cache(ttl=300)  # Cache for 5 minutes
def expensive_operation() -> dict:
    """Perform an expensive operation."""
    # Expensive computation or database query
    return {"result": result}
```

### 3. Connection Pooling

For database connections, use connection pooling:

```python
# Example with SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://user:password@localhost/dbname",
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)
```

### 4. Load Testing

Before deploying to production, perform load testing to identify bottlenecks:

```bash
# Using Apache Benchmark
ab -n 1000 -c 100 http://localhost:8000/api/endpoint
```

## Monitoring in Production {#monitoring-in-production}

APIFromAnything provides built-in monitoring capabilities that can be integrated with various monitoring systems.

### 1. Prometheus Integration

```python
from apifrom.monitoring import MetricsCollector, PrometheusExporter

# Create a metrics collector
metrics = MetricsCollector()

# Create a Prometheus exporter
prometheus_exporter = PrometheusExporter(collector=metrics)

# Define a metrics endpoint
@api(app)
def metrics() -> str:
    """Return Prometheus metrics."""
    return prometheus_exporter.export()
```

Configure Prometheus to scrape this endpoint:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'my-api'
    scrape_interval: 15s
    static_configs:
      - targets: ['my-api:8000']
```

### 2. Logging

Configure comprehensive logging:

```python
import logging
from apifrom.monitoring import LogExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='/var/log/my-api.log'
)

# Create a log exporter
log_exporter = LogExporter(collector=metrics)

# Export metrics periodically
log_exporter.export_periodic(interval_seconds=60)
```

### 3. Alerting

Set up alerts for critical metrics:

```yaml
# Prometheus alerting rules
groups:
- name: my-api-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(api_errors_total[5m]) / rate(api_requests_total[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is above 10% for the last 5 minutes"
```

### 4. Distributed Tracing

Implement distributed tracing for complex systems:

```python
from apifrom.monitoring.tracing import init_tracer, trace

# Initialize a tracer
tracer = init_tracer("my-api")

@api(app)
@trace(tracer)
def traced_endpoint() -> dict:
    """An endpoint with distributed tracing."""
    # Your endpoint logic
    return {"result": "success"}
```

## Production Deployment Checklist

Before deploying your APIFromAnything application to production, ensure you've completed the following checklist to guarantee a smooth, secure, and performant deployment:

### Security Checklist

- [ ] **Enable HTTPS**: Always use HTTPS in production
  ```python
  app.run(host="0.0.0.0", port=443, ssl_certfile="cert.pem", ssl_keyfile="key.pem")
  ```

- [ ] **Set up CORS properly**: Restrict CORS to only the domains that need access
  ```python
  from apifrom.middleware import CORSMiddleware
  
  app.add_middleware(
      CORSMiddleware(
          allow_origins=["https://yourdomain.com"],
          allow_methods=["GET", "POST", "PUT", "DELETE"],
          allow_headers=["Content-Type", "Authorization"],
          allow_credentials=True
      )
  )
  ```

- [ ] **Add CSRF protection**: Protect against Cross-Site Request Forgery
  ```python
  from apifrom.middleware import CSRFMiddleware
  
  app.add_middleware(CSRFMiddleware())
  ```

- [ ] **Configure security headers**: Add security headers to protect against common attacks
  ```python
  from apifrom.middleware import SecurityHeadersMiddleware
  
  app.add_middleware(SecurityHeadersMiddleware())
  ```

- [ ] **Set up rate limiting**: Protect against abuse and DoS attacks
  ```python
  from apifrom.middleware import RateLimitMiddleware
  
  app.add_middleware(
      RateLimitMiddleware(
          limit=100,  # 100 requests per minute
          window=60,
          by_ip=True
      )
  )
  ```

- [ ] **Implement authentication**: Secure your API with proper authentication
  ```python
  from apifrom.security import jwt_required
  
  @api(route="/protected", method="GET")
  @jwt_required(secret="your-secret-key")
  def protected_endpoint(request):
      user_id = request.state.jwt_payload.get("sub")
      return {"message": f"Hello, user {user_id}!"}
  ```

- [ ] **Validate input data**: Ensure all input data is properly validated
  ```python
  from pydantic import BaseModel, Field
  
  class User(BaseModel):
      name: str = Field(..., min_length=2, max_length=50)
      email: str = Field(..., regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
      age: int = Field(..., ge=18, le=120)
  
  @api(route="/users", method="POST")
  def create_user(user: User):
      # User data is automatically validated
      return {"id": 123, **user.dict()}
  ```

- [ ] **Use environment variables for secrets**: Never hardcode secrets in your code
  ```python
  import os
  from apifrom.security import jwt_required
  
  JWT_SECRET = os.environ.get("JWT_SECRET")
  
  @api(route="/protected", method="GET")
  @jwt_required(secret=JWT_SECRET)
  def protected_endpoint(request):
      return {"message": "Protected endpoint"}
  ```

### Performance Checklist

- [ ] **Enable caching**: Cache responses to improve performance
  ```python
  from apifrom.middleware import CacheMiddleware
  
  app.add_middleware(
      CacheMiddleware(
          ttl=60,  # Cache for 60 seconds
          max_size=1000  # Maximum number of cached responses
      )
  )
  ```

- [ ] **Use connection pooling**: Reuse connections to databases and external services
  ```python
  from apifrom.performance import ConnectionPool
  import aiohttp
  
  http_pool = ConnectionPool(
      factory=lambda: aiohttp.ClientSession(),
      min_size=5,
      max_size=20
  )
  ```

- [ ] **Enable compression**: Compress responses to reduce bandwidth usage
  ```python
  from apifrom.middleware import CompressionMiddleware
  
  app.add_middleware(CompressionMiddleware())
  ```

- [ ] **Implement pagination**: Paginate large result sets
  ```python
  @api(route="/users", method="GET")
  def get_users(page: int = 1, limit: int = 10):
      offset = (page - 1) * limit
      users = db.get_users(offset=offset, limit=limit)
      total = db.count_users()
      return {
          "users": users,
          "page": page,
          "limit": limit,
          "total": total,
          "pages": (total + limit - 1) // limit
      }
  ```

- [ ] **Use asynchronous programming**: Use async/await for I/O-bound operations
  ```python
  @api(route="/users", method="GET")
  async def get_users():
      async with db_pool.acquire() as connection:
          rows = await connection.fetch("SELECT * FROM users")
          return [dict(row) for row in rows]
  ```

- [ ] **Optimize database queries**: Use indexes and optimize queries
  ```python
  @api(route="/users", method="GET")
  async def get_users(search: str = None):
      query = "SELECT id, name, email FROM users"
      params = []
      
      if search:
          query += " WHERE name ILIKE $1 OR email ILIKE $1"
          params.append(f"%{search}%")
      
      query += " ORDER BY id LIMIT 100"
      
      async with db_pool.acquire() as connection:
          rows = await connection.fetch(query, *params)
          return [dict(row) for row in rows]
  ```

### Monitoring Checklist

- [ ] **Set up logging**: Configure proper logging for your application
  ```python
  import logging
  from apifrom.plugins import LoggingPlugin
  
  logging.basicConfig(
      level=logging.INFO,
      format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
      handlers=[
          logging.FileHandler("app.log"),
          logging.StreamHandler()
      ]
  )
  
  app.plugin_manager.register(LoggingPlugin())
  ```

- [ ] **Add metrics collection**: Collect metrics to monitor your API
  ```python
  from apifrom.monitoring import MetricsMiddleware
  
  app.add_middleware(MetricsMiddleware())
  
  @api(route="/metrics", method="GET")
  def metrics():
      return app.metrics.export_prometheus()
  ```

- [ ] **Set up health checks**: Add health check endpoints
  ```python
  @api(route="/health", method="GET")
  def health_check():
      # Check database connection
      db_status = check_database_connection()
      
      # Check external services
      external_services_status = check_external_services()
      
      status = "healthy" if db_status and external_services_status else "unhealthy"
      
      return {
          "status": status,
          "database": db_status,
          "external_services": external_services_status,
          "timestamp": datetime.datetime.now().isoformat()
      }
  ```

- [ ] **Configure error tracking**: Set up error tracking to be notified of errors
  ```python
  from apifrom.middleware import ErrorHandlingMiddleware
  
  def log_error(request, exc, traceback):
      # Send error to error tracking service
      error_tracking_service.capture_exception(exc)
  
  app.add_middleware(
      ErrorHandlingMiddleware(
          debug=False,
          log_exceptions=True,
          on_error=log_error
      )
  )
  ```

### Deployment Environment Checklist

- [ ] **Use environment-specific configuration**: Configure your application differently for different environments
  ```python
  import os
  
  # Get environment
  ENV = os.environ.get("ENV", "development")
  
  # Create API with environment-specific configuration
  app = API(
      title="My API",
      version="1.0.0",
      debug=ENV == "development"
  )
  
  # Add middleware based on environment
  if ENV == "production":
      app.add_middleware(SecurityHeadersMiddleware())
      app.add_middleware(RateLimitMiddleware(limit=100, window=60))
  ```

- [ ] **Set up a process manager**: Use a process manager to keep your application running
  ```bash
  # Using PM2
  pm2 start app.py --name "my-api" --interpreter python
  
  # Using Supervisor
  # Create a supervisor configuration file
  ```

- [ ] **Configure a reverse proxy**: Use a reverse proxy like Nginx or Apache
  ```nginx
  # Nginx configuration example
  server {
      listen 80;
      server_name api.example.com;
      
      location / {
          proxy_pass http://localhost:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
      }
  }
  ```

- [ ] **Set up SSL/TLS**: Configure SSL/TLS for HTTPS
  ```nginx
  # Nginx configuration with SSL
  server {
      listen 443 ssl;
      server_name api.example.com;
      
      ssl_certificate /path/to/certificate.crt;
      ssl_certificate_key /path/to/private.key;
      
      location / {
          proxy_pass http://localhost:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
      }
  }
  ```

- [ ] **Configure CORS headers in the reverse proxy**: Add CORS headers in the reverse proxy
  ```nginx
  # Nginx configuration with CORS
  server {
      listen 443 ssl;
      server_name api.example.com;
      
      # SSL configuration
      
      location / {
          proxy_pass http://localhost:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          
          # CORS headers
          add_header 'Access-Control-Allow-Origin' 'https://example.com';
          add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE';
          add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
          add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range';
          
          if ($request_method = 'OPTIONS') {
              add_header 'Access-Control-Max-Age' 1728000;
              add_header 'Content-Type' 'text/plain; charset=utf-8';
              add_header 'Content-Length' 0;
              return 204;
          }
      }
  }
  ```

### Final Checklist

- [ ] **Run tests**: Ensure all tests pass before deployment
  ```bash
  python -m pytest
  ```

- [ ] **Check for security vulnerabilities**: Scan your dependencies for vulnerabilities
  ```bash
  pip-audit
  ```

- [ ] **Verify documentation**: Ensure your API documentation is up-to-date
  ```python
  # Make sure your OpenAPI documentation is accessible
  app = API(
      title="My API",
      version="1.0.0",
      docs_url="/docs",
      openapi_url="/openapi.json"
  )
  ```

- [ ] **Create a rollback plan**: Have a plan for rolling back if something goes wrong
  ```bash
  # Example: Keep the previous version of your application
  cp -r /path/to/app /path/to/app.backup
  ```

- [ ] **Set up monitoring alerts**: Configure alerts for critical issues
  ```python
  # Example: Set up alerts for high error rates
  from apifrom.monitoring import AlertManager
  
  alert_manager = AlertManager()
  alert_manager.add_alert(
      name="high_error_rate",
      condition=lambda metrics: metrics.error_rate > 0.05,
      action=lambda: send_alert("High error rate detected!")
  )
  ```

- [ ] **Document deployment process**: Document the deployment process for future reference
  ```markdown
  # Deployment Process
  
  1. Run tests: `python -m pytest`
  2. Build the application: `python setup.py sdist bdist_wheel`
  3. Deploy to production: `scp dist/myapp-1.0.0.tar.gz user@server:/path/to/app`
  4. Install on the server: `pip install myapp-1.0.0.tar.gz`
  5. Restart the application: `systemctl restart myapp`
  ```

By following this checklist, you'll ensure that your APIFromAnything application is ready for production deployment with proper security, performance, and monitoring configurations.

---

By following this deployment guide, you can deploy your APIFromAnything applications to various environments with confidence, ensuring they are performant, scalable, and properly monitored. 