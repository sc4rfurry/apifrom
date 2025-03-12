"""
Security headers and XSS protection example using APIFromAnything.

This example demonstrates how to use the security headers and XSS protection
features of the APIFromAnything library to protect an API against various
web vulnerabilities.
"""

import logging
from typing import Dict, List, Optional

from apifrom import API, api
from apifrom.security import (
    ContentSecurityPolicy,
    ReferrerPolicy,
    XSSProtection,
    SecurityHeadersMiddleware,
    XSSFilter,
    XSSProtectionMiddleware,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create API instance
app = API(
    title="Secure Headers API Example",
    description="An API with security headers and XSS protection created with APIFromAnything",
    version="1.0.0",
    debug=True
)

# Create a Content Security Policy
csp = ContentSecurityPolicy()
csp.default_src().allow_self()
csp.script_src().allow_self().allow_sources("https://cdn.jsdelivr.net", "https://unpkg.com")
csp.style_src().allow_self().allow_sources("https://cdn.jsdelivr.net", "https://unpkg.com")
csp.img_src().allow_self().allow_sources("https://via.placeholder.com", "data:")
csp.font_src().allow_self().allow_sources("https://fonts.gstatic.com")
csp.connect_src().allow_self()
csp.object_src().allow_none()
csp.frame_ancestors().allow_self()
csp.form_action().allow_self()
csp.base_uri().allow_self()

# Add security headers middleware
security_headers_middleware = SecurityHeadersMiddleware(
    content_security_policy=csp,
    x_frame_options="DENY",
    x_content_type_options="nosniff",
    referrer_policy=ReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN,
    x_xss_protection=XSSProtection.ENABLED_BLOCK,
    strict_transport_security="max-age=31536000; includeSubDomains",
    permissions_policy={
        "camera": [],
        "microphone": [],
        "geolocation": [],
        "payment": [],
    },
    exempt_paths=["/api/exempt"],
    exempt_content_types=["application/octet-stream"],
)
app.add_middleware(security_headers_middleware)

# Add XSS protection middleware
xss_protection_middleware = XSSProtectionMiddleware(
    sanitize_json_response=True,
    sanitize_html_response=True,
    allowed_html_tags={
        "a", "b", "br", "code", "div", "em", "h1", "h2", "h3", "h4", "h5", "h6",
        "i", "li", "ol", "p", "pre", "span", "strong", "ul",
    },
    allowed_html_attributes={
        "a": {"href", "title", "target", "rel"},
        "*": {"class", "id"},
    },
    exempt_paths=["/api/exempt"],
)
app.add_middleware(xss_protection_middleware)

# Simulated database
articles_db = [
    {
        "id": 1,
        "title": "Introduction to Web Security",
        "content": "Web security is important for protecting your applications from attacks.",
        "author": "John Doe",
    },
    {
        "id": 2,
        "title": "Content Security Policy",
        "content": "Content Security Policy (CSP) is a security feature that helps prevent XSS attacks.",
        "author": "Jane Smith",
    },
    {
        "id": 3,
        "title": "Cross-Site Scripting",
        "content": "Cross-Site Scripting (XSS) is a type of security vulnerability that allows attackers to inject malicious code.",
        "author": "Bob Johnson",
    },
]


@api(route="/api/articles", method="GET")
def get_articles() -> List[Dict]:
    """
    Get all articles.
    
    Returns:
        A list of articles
    """
    logger.info("Fetching articles")
    return articles_db


@api(route="/api/articles/{article_id}", method="GET")
def get_article(article_id: int) -> Dict:
    """
    Get an article by ID.
    
    Args:
        article_id: The ID of the article to retrieve
        
    Returns:
        An article
    """
    logger.info(f"Fetching article {article_id}")
    
    for article in articles_db:
        if article["id"] == article_id:
            return article
    
    return {"error": "Article not found"}


@api(route="/api/articles", method="POST")
def create_article(title: str, content: str, author: str) -> Dict:
    """
    Create a new article.
    
    This endpoint demonstrates XSS protection by sanitizing the input.
    
    Args:
        title: The title of the article
        content: The content of the article
        author: The author of the article
        
    Returns:
        The created article
    """
    logger.info(f"Creating new article: {title}")
    
    # Sanitize input to prevent XSS attacks
    title = XSSFilter.escape_html(title)
    content = XSSFilter.sanitize_html(content)
    author = XSSFilter.escape_html(author)
    
    article_id = max(article["id"] for article in articles_db) + 1
    new_article = {"id": article_id, "title": title, "content": content, "author": author}
    articles_db.append(new_article)
    
    return new_article


@api(route="/api/articles/{article_id}", method="PUT")
def update_article(article_id: int, title: Optional[str] = None, content: Optional[str] = None, author: Optional[str] = None) -> Dict:
    """
    Update an article.
    
    This endpoint demonstrates XSS protection by sanitizing the input.
    
    Args:
        article_id: The ID of the article to update
        title: The new title of the article (optional)
        content: The new content of the article (optional)
        author: The new author of the article (optional)
        
    Returns:
        The updated article
    """
    logger.info(f"Updating article {article_id}")
    
    for article in articles_db:
        if article["id"] == article_id:
            if title is not None:
                article["title"] = XSSFilter.escape_html(title)
            if content is not None:
                article["content"] = XSSFilter.sanitize_html(content)
            if author is not None:
                article["author"] = XSSFilter.escape_html(author)
            return article
    
    return {"error": "Article not found"}


@api(route="/api/exempt/articles", method="GET")
def get_exempt_articles() -> List[Dict]:
    """
    Get all articles (exempt from security headers and XSS protection).
    
    This endpoint is exempt from security headers and XSS protection.
    
    Returns:
        A list of articles
    """
    logger.info("Fetching articles (exempt)")
    return articles_db


@api(route="/api/xss-test", method="GET")
def get_xss_test() -> Dict:
    """
    Test XSS protection.
    
    This endpoint returns a response with potential XSS payloads,
    which should be sanitized by the XSS protection middleware.
    
    Returns:
        A response with potential XSS payloads
    """
    logger.info("Testing XSS protection")
    
    return {
        "safe_string": "This is a safe string",
        "xss_string": "<script>alert('XSS')</script>",
        "nested_xss": {
            "xss_string": "<img src='x' onerror='alert(\"XSS\")'>",
            "list_with_xss": [
                "Safe item",
                "<script>document.cookie</script>",
                {"xss": "<iframe src='javascript:alert(\"XSS\")'>"},
            ],
        },
    }


@api(route="/api/html", method="GET")
def get_html() -> str:
    """
    Get an HTML page.
    
    This endpoint returns an HTML page with security headers.
    
    Returns:
        An HTML page
    """
    logger.info("Fetching HTML page")
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Secure Headers Example</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
            }
            h1 {
                color: #333;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Secure Headers Example</h1>
            <p>This page is served with security headers to protect against various web vulnerabilities.</p>
            
            <h2>Security Headers</h2>
            <ul>
                <li><strong>Content-Security-Policy:</strong> Prevents XSS attacks by controlling which resources can be loaded.</li>
                <li><strong>X-Frame-Options:</strong> Prevents clickjacking by controlling whether the page can be framed.</li>
                <li><strong>X-Content-Type-Options:</strong> Prevents MIME type sniffing by ensuring the declared content type is followed.</li>
                <li><strong>Referrer-Policy:</strong> Controls how much referrer information is included with requests.</li>
                <li><strong>X-XSS-Protection:</strong> Provides protection against XSS attacks in older browsers.</li>
                <li><strong>Strict-Transport-Security:</strong> Ensures the page is only accessed over HTTPS.</li>
                <li><strong>Permissions-Policy:</strong> Controls which browser features can be used by the page.</li>
            </ul>
            
            <h2>Articles</h2>
            <div id="articles"></div>
            
            <script>
                // Fetch articles from the API
                fetch('/api/articles')
                    .then(response => response.json())
                    .then(articles => {
                        const articlesContainer = document.getElementById('articles');
                        articles.forEach(article => {
                            const articleElement = document.createElement('div');
                            articleElement.innerHTML = `
                                <h3>${article.title}</h3>
                                <p>${article.content}</p>
                                <p><em>By ${article.author}</em></p>
                                <hr>
                            `;
                            articlesContainer.appendChild(articleElement);
                        });
                    })
                    .catch(error => console.error('Error fetching articles:', error));
            </script>
        </div>
    </body>
    </html>
    """


@api(route="/api/unsafe-html", method="POST")
def create_unsafe_html(html: str) -> Dict:
    """
    Create unsafe HTML.
    
    This endpoint demonstrates XSS protection by sanitizing the input.
    
    Args:
        html: The HTML to sanitize
        
    Returns:
        The sanitized HTML
    """
    logger.info("Creating unsafe HTML")
    
    # Sanitize the HTML
    sanitized_html = XSSFilter.sanitize_html(html)
    
    return {
        "original_html": html,
        "sanitized_html": sanitized_html,
    }


if __name__ == "__main__":
    # Run the API server
    app.run(host="0.0.0.0", port=8008) 