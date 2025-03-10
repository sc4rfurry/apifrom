# <div align="center">🚀 APIFromAnything</div>

<div align="center">
  <img src="https://img.shields.io/badge/APIFromAnything-Transform%20Python%20Functions%20to%20APIs-blue?style=for-the-badge&logo=python" alt="APIFromAnything" />
  <br/>
  <strong>Transform any Python function into a production-ready REST API endpoint in seconds</strong>
</div>

<p align="center">
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License: MIT" />
  </a>
  <a href="https://pypi.org/project/apifrom/">
    <img src="https://img.shields.io/badge/version-0.1.0-brightgreen.svg?style=flat-square" alt="Version" />
  </a>
  <a href="#python-versions">
    <img src="https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10-blue?style=flat-square&logo=python" alt="Python Versions" />
  </a>
  <a href="#status">
    <img src="https://img.shields.io/badge/status-production--ready-green?style=flat-square" alt="Status" />
  </a>
  <a href="#documentation">
    <img src="https://img.shields.io/badge/docs-passing-brightgreen?style=flat-square&logo=readthedocs" alt="Docs Status" />
  </a>
  <br/>
  <a href="#code-style">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square" alt="Code Style: Black" />
  </a>
  <a href="#contributors">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" alt="PRs Welcome" />
  </a>
  <a href="https://github.com/sc4rfurry/apifrom/stargazers">
    <img src="https://img.shields.io/github/stars/apifrom/apifrom?style=flat-square" alt="GitHub stars" />
  </a>
</p>

<div align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-why-apifrom">Why APIFromAnything?</a> •
  <a href="#-key-features">Key Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-examples">Examples</a> •
  <a href="#-advanced-features">Advanced Features</a> •
  <a href="#-performance-optimization">Performance</a> •
  <a href="#-documentation">Documentation</a> •
  <a href="#-community">Community</a> •
  <a href="#-contributing">Contributing</a> •
  <a href="#-license">License</a>
</div>

---

## 🚀 Overview

**APIFromAnything** is a production-grade Python library that transforms ordinary Python functions into fully-functional REST API endpoints using a decorator-based approach. It's designed to be robust, extensible, and high-performance, with features like automatic routing, input validation, output serialization, error handling, and documentation generation.

<div align="center">
  <img src="https://img.shields.io/badge/From%20Function%20to%20API-In%20Seconds-purple?style=for-the-badge" alt="From Function to API in Seconds" />
</div>

```python
from apifrom import API, api

app = API(title="My API")

@api(route="/hello/{name}")
def hello(name: str, greeting: str = "Hello") -> dict:
    """Say hello to someone."""
    return {"message": f"{greeting}, {name}!"}

```

## ⚡ Getting Started in 30 Seconds

1. **Install the package**:
   ```bash
   pip install apifrom
   ```

2. **Create your API** (`app.py`):
   ```python
   from apifrom import API, api

   app = API(title="Quick Start API")

   @api(route="/hello/{name}")
   def hello(name: str, greeting: str = "Hello") -> dict:
       return {"message": f"{greeting}, {name}!"}

   if __name__ == "__main__":
       app.run()
   ```

3. **Run your API**:
   ```bash
   python app.py
   ```

4. **Test your API**:
   ```bash
   curl "http://localhost:8000/hello/World?greeting=Hi"
   # {"message": "Hi, World!"}
   ```

5. **View API documentation** at `http://localhost:8000/docs`

## 🤔 Why APIFromAnything?

<table>
  <tr>
    <td><b>🧠 Intuitive Design</b></td>
    <td>Simple decorator-based API that feels natural to Python developers</td>
  </tr>
  <tr>
    <td><b>⚡ Lightning Fast Development</b></td>
    <td>Create production-ready APIs in minutes instead of hours or days</td>
  </tr>
  <tr>
    <td><b>🛡️ Built-in Security</b></td>
    <td>Comprehensive security features including JWT, OAuth2, API keys, and more</td>
  </tr>
  <tr>
    <td><b>🔍 Type-Based Validation</b></td>
    <td>Automatic request validation using Python type hints and Pydantic models</td>
  </tr>
  <tr>
    <td><b>🔌 Extensible Plugin System</b></td>
    <td>Powerful plugin architecture for customizing and extending functionality</td>
  </tr>
  <tr>
    <td><b>☁️ Cloud-Ready</b></td>
    <td>Deploy to AWS Lambda, Google Cloud Functions, Azure, Vercel, or Netlify with ease</td>
  </tr>
  <tr>
    <td><b>📊 Built-in Monitoring</b></td>
    <td>Comprehensive metrics and monitoring capabilities out of the box</td>
  </tr>
</table>

## ✨ Key Features

<table>
  <tr>
    <td><b>🧩 Simple Decorator API</b></td>
    <td>Transform any Python function into an API endpoint with a single decorator</td>
  </tr>
  <tr>
    <td><b>🔍 Type-Based Validation</b></td>
    <td>Automatic request validation based on Python type hints</td>
  </tr>
  <tr>
    <td><b>🔄 Automatic Serialization</b></td>
    <td>Convert Python objects to JSON responses automatically</td>
  </tr>
  <tr>
    <td><b>🛣️ Path & Query Parameters</b></td>
    <td>Support for path and query parameters with automatic type conversion</td>
  </tr>
  <tr>
    <td><b>⚡ Asynchronous Support</b></td>
    <td>First-class support for async/await functions</td>
  </tr>
  <tr>
    <td><b>🔌 Middleware System</b></td>
    <td>Extensible middleware system for request/response processing</td>
  </tr>
  <tr>
    <td><b>🔒 Security Features</b></td>
    <td>Built-in support for JWT, API key, Basic auth, OAuth2, CORS, CSRF, security headers, and more</td>
  </tr>
  <tr>
    <td><b>📚 OpenAPI Documentation</b></td>
    <td>Automatic generation of OpenAPI/Swagger documentation</td>
  </tr>
  <tr>
    <td><b>📊 Monitoring & Metrics</b></td>
    <td>Track API performance and usage with comprehensive metrics collection</td>
  </tr>
  <tr>
    <td><b>🚀 Performance Optimization</b></td>
    <td>Tools for profiling, caching, connection pooling, and batch processing</td>
  </tr>
  <tr>
    <td><b>☁️ Serverless Ready</b></td>
    <td>Deploy to AWS Lambda, Google Cloud Functions, Azure Functions, Vercel, and Netlify</td>
  </tr>
  <tr>
    <td><b>🔌 Plugin System</b></td>
    <td>Extend and customize functionality with a powerful plugin architecture</td>
  </tr>
</table>

## 📦 Installation

<details open>
<summary><b>Standard Installation</b></summary>

```bash
pip install apifrom
```
</details>

<details>
<summary><b>With Optional Dependencies</b></summary>

```bash
# With database support (SQLAlchemy, PostgreSQL, MySQL, SQLite)
pip install "apifrom[database]"

# With caching support (Redis)
pip install "apifrom[cache]"

# With monitoring support (Prometheus)
pip install "apifrom[monitoring]"

# With development tools
pip install "apifrom[dev]"

# With all optional dependencies
pip install "apifrom[all]"
```
</details>

<details>
<summary><b>From Source</b></summary>

```bash
git clone https://github.com/sc4rfurry/apifrom.git
cd apifrom
pip install -e .
```
</details>

## 🏁 Quick Start

Create a file named `app.py`:

```python
from apifrom import API, api

# Create an API instance
app = API(
    title="My API",
    description="A simple API created with APIFromAnything",
    version="1.0.0"
)

# Define an API endpoint
@api(route="/hello/{name}", method="GET")
def hello(name: str, greeting: str = "Hello") -> dict:
    """
    Say hello to someone.
    
    Args:
        name: The name to greet
        greeting: The greeting to use (default: "Hello")
        
    Returns:
        A greeting message
    """
    return {"message": f"{greeting}, {name}!"}

# Run the API server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

Run the application:

```bash
python app.py
```

Test the API:

```bash
curl "http://localhost:8000/hello/World?greeting=Hi"
# {"message": "Hi, World!"}
```

Or visit the automatic Swagger documentation at `http://localhost:8000/docs`.

## 💡 Real-World Use Cases

<details>
<summary><b>Microservice Architecture</b></summary>

APIFromAnything is perfect for building microservices that need to expose REST APIs. Its lightweight nature and high performance make it ideal for containerized environments.

```python
from apifrom import API, api
from apifrom.middleware import CORSMiddleware
from services import OrderService

app = API(title="Order Service")

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware(
        allow_origins=["https://frontend.example.com"],
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"]
    )
)

# Inject the order service
order_service = OrderService()

@api(route="/orders", method="GET")
async def get_orders(user_id: str = None, status: str = None):
    """Get orders with optional filtering."""
    return await order_service.get_orders(user_id=user_id, status=status)

@api(route="/orders/{order_id}", method="GET")
async def get_order(order_id: str):
    """Get a specific order by ID."""
    return await order_service.get_order(order_id)

@api(route="/orders", method="POST")
async def create_order(user_id: str, items: list, shipping_address: dict):
    """Create a new order."""
    return await order_service.create_order(
        user_id=user_id,
        items=items,
        shipping_address=shipping_address
    )
```
</details>

<details>
<summary><b>Data Science API</b></summary>

Expose machine learning models as APIs with minimal effort:

```python
from apifrom import API, api
import joblib
import numpy as np

app = API(title="ML Model API")

# Load the pre-trained model
model = joblib.load("model.pkl")

@api(route="/predict", method="POST")
def predict(features: list) -> dict:
    """
    Make a prediction using the pre-trained model.
    
    Args:
        features: List of numerical features
        
    Returns:
        Prediction result
    """
    # Convert to numpy array and reshape for single sample
    X = np.array(features).reshape(1, -1)
    
    # Make prediction
    prediction = model.predict(X)[0]
    probability = model.predict_proba(X)[0].max()
    
    return {
        "prediction": int(prediction),
        "probability": float(probability),
        "features": features
    }
```
</details>

<details>
<summary><b>API Gateway</b></summary>

Create an API gateway that routes requests to different services:

```python
from apifrom import API, api
from apifrom.middleware import RateLimitMiddleware
import httpx

app = API(title="API Gateway")

# Add rate limiting
app.add_middleware(
    RateLimitMiddleware(
        limit=100,  # 100 requests per minute
        window=60
    )
)

# Service endpoints
SERVICES = {
    "users": "http://user-service:8001",
    "orders": "http://order-service:8002",
    "products": "http://product-service:8003"
}

@api(route="/{service}/{path:path}", method=["GET", "POST", "PUT", "DELETE"])
async def gateway(request, service: str, path: str):
    """
    Gateway endpoint that routes requests to the appropriate service.
    """
    if service not in SERVICES:
        return {"error": f"Service '{service}' not found"}, 404
    
    # Forward the request to the appropriate service
    async with httpx.AsyncClient() as client:
        service_url = f"{SERVICES[service]}/{path}"
        
        # Forward the request with the same method, headers, and body
        response = await client.request(
            method=request.method,
            url=service_url,
            headers=request.headers,
            params=request.query_params,
            json=await request.json() if request.body else None
        )
        
        # Return the response from the service
        return response.json(), response.status_code
```
</details>

## 📚 Documentation

<details>
<summary><b>For more detailed documentation, please visit <a href="/docs/">the documentation site</a>.</b></summary>

The documentation includes:

- **Getting Started Guide**: Quick start and basic concepts
- **API Reference**: Detailed reference for all modules and functions
- **Tutorials**: Step-by-step guides for common tasks
- **Examples**: Complete examples for various use cases
- **Deployment Guide**: How to deploy to different environments
- **Migration Guide**: How to migrate from other frameworks
- **FAQ**: Frequently asked questions
</details>

## 🤝 Contributing

<details>
<summary><b>We welcome contributions!</b></summary>

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/awesome-feature`
3. Commit your changes: `git commit -am 'Add awesome feature'`
4. Push to the branch: `git push origin feature/awesome-feature`
5. Submit a pull request

Please make sure to follow our [code of conduct](CODE_OF_CONDUCT.md) and [contribution guidelines](CONTRIBUTING.md).
</details>

<details>
<summary><b>Development Setup</b></summary>

```bash
# Clone the repository
git clone https://github.com/sc4rfurry/apifrom.git
cd apifrom

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
black .
flake8
mypy .
```
</details>

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<details>
<summary><b>MIT License</b></summary>

```
MIT License

Copyright (c) 2023 sc4rfurry

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
</details>

## 👥 Community

<div align="center">
  <table>
    <tr>
    <tr>
      <td align="center">
        <a href="https://github.com/sc4rfurry/apifrom/discussions">
          <img src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github" alt="GitHub Discussions" />
        </a>
        <p>Participate in discussions and share your ideas</p>
      </td>
      <td align="center">
        <a href="/docs/">
          <img src="https://img.shields.io/badge/Documentation-Read%20the%20Docs-8CA1AF?style=for-the-badge&logo=read-the-docs" alt="Read the Docs" />
        </a>
        <p>Read our comprehensive documentation</p>
      </td>
    </tr>
  </table>
</div>

<hr>
<div align="center">
  <p>Made with ❤️ by the sc4rfurry</p>
  <p>
    <a href="https://github.com/sc4rfurry/apifrom/stargazers">
      <img src="https://img.shields.io/github/stars/apifrom/apifrom?style=social" alt="GitHub stars" />
    </a>
    <a href="https://github.com/sc4rfurry/apifrom/network/members">
      <img src="https://img.shields.io/github/forks/apifrom/apifrom?style=social" alt="GitHub forks" />
    </a>
    <a href="https://github.com/sc4rfurry/apifrom/watchers">
      <img src="https://img.shields.io/github/watchers/apifrom/apifrom?style=social" alt="GitHub watchers" />
    </a>
  </p>
</div>