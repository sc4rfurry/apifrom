# Serverless Deployment

APIFromAnything includes adapters for popular serverless platforms, allowing you to deploy your APIs to various cloud providers with minimal configuration.

## Overview

Serverless computing allows you to build and run applications without thinking about servers. It eliminates infrastructure management tasks such as server provisioning, patching, operating system maintenance, and capacity provisioning. APIFromAnything makes it easy to deploy your APIs to serverless platforms by providing adapters that handle the integration with the platform's event model.

## Supported Platforms

APIFromAnything currently supports the following serverless platforms:

- **AWS Lambda**: Amazon's serverless compute service
- **Google Cloud Functions**: Google Cloud's serverless compute service
- **Azure Functions**: Microsoft Azure's serverless compute service
- **Vercel**: A platform for frontend frameworks and static sites
- **Netlify**: A platform for modern web projects

## Async Support in Serverless Environments

As of version 1.0.0, APIFromAnything provides full async/await support in all serverless adapters. This allows you to use async functions in your API endpoints when deploying to serverless platforms.

```python
from apifrom import API, api
from apifrom.adapters import LambdaAdapter
import asyncio

app = API(title="Async Serverless API")

@api(route="/async-hello/{name}", method="GET")
async def async_hello(name: str):
    # Simulate an async operation
    await asyncio.sleep(1)
    return {"message": f"Hello, {name}!", "async": True}

# Create a Lambda handler
lambda_adapter = LambdaAdapter(app)

def handler(event, context):
    return lambda_adapter.handle(event, context)
```

The serverless adapters will automatically handle the async nature of your functions, ensuring that they are properly awaited before returning a response.

## AWS Lambda

The `LambdaAdapter` allows you to deploy your API to AWS Lambda.

### Basic Usage

```python
from apifrom import API, api
from apifrom.adapters import LambdaAdapter

# Create an API
app = API(title="Serverless API")

@api(route="/hello/{name}", method="GET")
def hello(name: str):
    return {"message": f"Hello, {name}!"}

# Create a Lambda handler
lambda_adapter = LambdaAdapter(app)

def handler(event, context):
    return lambda_adapter.handle(event, context)
```

### Deployment

1. **Create a deployment package**:

   ```bash
   pip install -t package/ apifrom
   cp lambda_function.py package/
   cd package
   zip -r ../deployment.zip .
   ```

2. **Create a Lambda function**:

   - Go to the AWS Lambda console
   - Click "Create function"
   - Choose "Author from scratch"
   - Enter a name for your function
   - Choose Python 3.9 as the runtime
   - Click "Create function"
   - Upload the deployment.zip file

3. **Configure API Gateway**:

   - Go to the API Gateway console
   - Click "Create API"
   - Choose "REST API" and click "Build"
   - Enter a name for your API
   - Click "Create API"
   - Click "Create Resource" and configure your resource path
   - Click "Create Method" and configure your method
   - Select "Lambda Function" as the integration type
   - Select your Lambda function
   - Click "Save"
   - Click "Deploy API" to deploy your API

### Advanced Configuration

The `LambdaAdapter` supports various configuration options:

```python
lambda_adapter = LambdaAdapter(
    app,
    strip_stage_path=True,  # Strip the stage path from the request path
    enable_binary_response=True,  # Enable binary responses
    binary_mime_types=["application/octet-stream"],  # MIME types to treat as binary
    enable_cors=True,  # Enable CORS
    cors_origins=["*"],  # CORS allowed origins
    cors_headers=["Content-Type", "Authorization"],  # CORS allowed headers
    cors_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # CORS allowed methods
    cors_max_age=3600,  # CORS max age
    cors_allow_credentials=True,  # CORS allow credentials
)
```

## Google Cloud Functions

The `CloudFunctionAdapter` allows you to deploy your API to Google Cloud Functions.

### Basic Usage

```python
from apifrom import API, api
from apifrom.adapters import CloudFunctionAdapter

# Create an API
app = API(title="Serverless API")

@api(route="/hello/{name}", method="GET")
def hello(name: str):
    return {"message": f"Hello, {name}!"}

# Create a Cloud Function handler
cloud_function_adapter = CloudFunctionAdapter(app)

def handler(request):
    return cloud_function_adapter.handle(request)
```

### Deployment

1. **Create a deployment package**:

   ```bash
   # Create a requirements.txt file
   echo "apifrom" > requirements.txt
   
   # Create a main.py file with your handler
   ```

2. **Deploy to Google Cloud Functions**:

   ```bash
   gcloud functions deploy hello \
       --runtime python39 \
       --trigger-http \
       --allow-unauthenticated \
       --entry-point handler
   ```

### Advanced Configuration

The `CloudFunctionAdapter` supports various configuration options:

```python
cloud_function_adapter = CloudFunctionAdapter(
    app,
    enable_binary_response=True,  # Enable binary responses
    binary_mime_types=["application/octet-stream"],  # MIME types to treat as binary
    enable_cors=True,  # Enable CORS
    cors_origins=["*"],  # CORS allowed origins
    cors_headers=["Content-Type", "Authorization"],  # CORS allowed headers
    cors_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # CORS allowed methods
    cors_max_age=3600,  # CORS max age
    cors_allow_credentials=True,  # CORS allow credentials
)
```

## Azure Functions

The `AzureFunctionAdapter` allows you to deploy your API to Azure Functions.

### Basic Usage

```python
from apifrom import API, api
from apifrom.adapters import AzureFunctionAdapter

# Create an API
app = API(title="Serverless API")

@api(route="/hello/{name}", method="GET")
def hello(name: str):
    return {"message": f"Hello, {name}!"}

# Create an Azure Function handler
azure_function_adapter = AzureFunctionAdapter(app)

def main(req):
    return azure_function_adapter.handle(req)
```

### Deployment

1. **Create a deployment package**:

   ```bash
   # Create a requirements.txt file
   echo "apifrom" > requirements.txt
   
   # Create a function.json file
   ```

2. **Deploy to Azure Functions**:

   ```bash
   func azure functionapp publish <app-name>
   ```

### Advanced Configuration

The `AzureFunctionAdapter` supports various configuration options:

```python
azure_function_adapter = AzureFunctionAdapter(
    app,
    enable_binary_response=True,  # Enable binary responses
    binary_mime_types=["application/octet-stream"],  # MIME types to treat as binary
    enable_cors=True,  # Enable CORS
    cors_origins=["*"],  # CORS allowed origins
    cors_headers=["Content-Type", "Authorization"],  # CORS allowed headers
    cors_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # CORS allowed methods
    cors_max_age=3600,  # CORS max age
    cors_allow_credentials=True,  # CORS allow credentials
)
```

## Vercel

The `VercelAdapter` allows you to deploy your API to Vercel.

### Basic Usage

```python
from apifrom import API, api
from apifrom.adapters import VercelAdapter

# Create an API
app = API(title="Serverless API")

@api(route="/api/hello", method="GET")
def hello(name: str = "World"):
    return {"message": f"Hello, {name}!"}

# Create a Vercel handler
vercel_adapter = VercelAdapter(app)

def handler(req):
    return vercel_adapter.handle(req)
```

### Deployment

1. **Create a deployment package**:

   ```bash
   # Create a requirements.txt file
   echo "apifrom" > requirements.txt
   
   # Create an api/hello.py file with your handler
   ```

2. **Deploy to Vercel**:

   ```bash
   vercel
   ```

### Advanced Configuration

The `VercelAdapter` supports various configuration options:

```python
vercel_adapter = VercelAdapter(
    app,
    enable_binary_response=True,  # Enable binary responses
    binary_mime_types=["application/octet-stream"],  # MIME types to treat as binary
    enable_cors=True,  # Enable CORS
    cors_origins=["*"],  # CORS allowed origins
    cors_headers=["Content-Type", "Authorization"],  # CORS allowed headers
    cors_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # CORS allowed methods
    cors_max_age=3600,  # CORS max age
    cors_allow_credentials=True,  # CORS allow credentials
)
```

## Netlify

The `NetlifyAdapter` allows you to deploy your API to Netlify Functions.

### Basic Usage

```python
from apifrom import API, api
from apifrom.adapters import NetlifyAdapter

# Create an API
app = API(title="Serverless API")

@api(route="/.netlify/functions/hello", method="GET")
def hello(name: str = "World"):
    return {"message": f"Hello, {name}!"}

# Create a Netlify handler
netlify_adapter = NetlifyAdapter(app)

def handler(event, context):
    return netlify_adapter.handle(event, context)
```

### Deployment

1. **Create a deployment package**:

   ```bash
   # Create a requirements.txt file
   echo "apifrom" > requirements.txt
   
   # Create a netlify.toml file
   ```

2. **Deploy to Netlify**:

   ```bash
   netlify deploy --prod
   ```

### Advanced Configuration

The `NetlifyAdapter` supports various configuration options:

```python
netlify_adapter = NetlifyAdapter(
    app,
    strip_function_path=True,  # Strip the function path from the request path
    enable_binary_response=True,  # Enable binary responses
    binary_mime_types=["application/octet-stream"],  # MIME types to treat as binary
    enable_cors=True,  # Enable CORS
    cors_origins=["*"],  # CORS allowed origins
    cors_headers=["Content-Type", "Authorization"],  # CORS allowed headers
    cors_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # CORS allowed methods
    cors_max_age=3600,  # CORS max age
    cors_allow_credentials=True,  # CORS allow credentials
)
```

## Best Practices

### Cold Start Optimization

Serverless functions can experience "cold starts" when they haven't been used for a while. Here are some tips to minimize cold start times:

1. **Keep your dependencies minimal**: Only include the dependencies you need
2. **Use a smaller runtime**: Python 3.9 has faster startup times than Python 3.8
3. **Optimize your code**: Minimize the amount of code that runs during initialization
4. **Use connection pooling**: Reuse connections to databases and other services
5. **Use caching**: Cache expensive operations

### Error Handling

Make sure to handle errors properly in your serverless functions:

```python
from apifrom import API, api
from apifrom.middleware import ErrorHandlingMiddleware

# Create an API
app = API(title="Serverless API")

# Add error handling middleware
app.add_middleware(
    ErrorHandlingMiddleware(
        debug=False,  # Disable debug mode in production
        include_traceback=False,  # Don't include tracebacks in production
        log_exceptions=True  # Log exceptions
    )
)

@api(route="/hello/{name}", method="GET")
def hello(name: str):
    if not name:
        raise ValueError("Name cannot be empty")
    return {"message": f"Hello, {name}!"}
```

### Logging

Use proper logging in your serverless functions:

```python
import logging
from apifrom import API, api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create an API
app = API(title="Serverless API")

@api(route="/hello/{name}", method="GET")
def hello(name: str):
    logger.info(f"Received request for name: {name}")
    return {"message": f"Hello, {name}!"}
```

### Security

Make sure to secure your serverless functions:

```python
from apifrom import API, api
from apifrom.security import jwt_required

# Create an API
app = API(title="Serverless API")

@api(route="/hello/{name}", method="GET")
@jwt_required(secret="your-secret-key", algorithm="HS256")
def hello(request, name: str):
    user = request.state.jwt_payload.get("sub")
    return {"message": f"Hello, {name}! You are authenticated as {user}"}
```

## Conclusion

APIFromAnything makes it easy to deploy your APIs to various serverless platforms. By using the provided adapters, you can focus on building your API without worrying about the underlying infrastructure. 