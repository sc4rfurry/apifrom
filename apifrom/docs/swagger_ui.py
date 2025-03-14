"""
Swagger UI integration for APIFromAnything.

This module provides a highly customizable Swagger UI integration for APIs created 
with the APIFromAnything library, with advanced styling and branding options.
"""

import os
import json
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from apifrom.docs.openapi import OpenAPIGenerator


class SwaggerUIConfig:
    """
    Configuration for Swagger UI customization.
    
    This class provides extensive configuration options for customizing the 
    appearance and behavior of the Swagger UI documentation.
    """
    
    def __init__(
        self,
        theme: str = "default",
        deep_linking: bool = True,
        display_operation_id: bool = False,
        default_models_expand_depth: int = 1,
        default_model_expand_depth: int = 1,
        default_model_rendering: str = "example",
        display_request_duration: bool = True,
        doc_expansion: str = "list",
        filter: bool = True,
        max_displayed_tags: Optional[int] = None,
        operations_sorter: Optional[str] = None,
        show_extensions: bool = False,
        show_common_extensions: bool = False,
        tag_sorter: Optional[str] = None,
        use_unicode_characters: bool = True,
        persist_authorization: bool = False,
        syntax_highlight: str = "monokai",
        oauth2_redirect_url: Optional[str] = None,
        custom_css: Optional[str] = None,
        custom_js: Optional[str] = None,
        custom_favicon: Optional[str] = None,
        custom_swagger_ui_version: str = "5.9.1",
        dom_id: str = "#swagger-ui",
        layout: str = "StandaloneLayout",
        plugins: Optional[List[str]] = None,
        presets: Optional[List[str]] = None,
    ):
        """
        Initialize the Swagger UI configuration.
        
        Args:
            theme: The theme to use (default, material, muted, outline, flattop)
            deep_linking: If set to true, enables deep linking for tags and operations
            display_operation_id: Controls the display of operationId in operations list
            default_models_expand_depth: The default expansion depth for models (set to -1 completely hide the models)
            default_model_expand_depth: The default expansion depth for the model on the model-example section
            default_model_rendering: Controls how the model is shown when the API is first rendered
            display_request_duration: Controls the display of the request duration (in milliseconds) for Try-It-Out requests
            doc_expansion: Controls the default expansion setting for the operations and tags
            filter: If set, enables filtering. The top bar will show an edit box that you can use to filter the tagged operations that are shown
            max_displayed_tags: If set, limits the number of tagged operations displayed to at most this many
            operations_sorter: Apply a sort to the operation list of each API
            show_extensions: Controls the display of vendor extension (x-) fields and values
            show_common_extensions: Controls the display of extensions (pattern, maxLength, minLength, maximum, minimum) fields and values
            tag_sorter: Apply a sort to the tag list
            use_unicode_characters: Controls whether unicode characters are used in rendered descriptions
            persist_authorization: If set, will persist authorization data
            syntax_highlight: Syntax highlighting theme (agate, arta, monokai, nord, obsidian, etc.)
            oauth2_redirect_url: OAuth2 redirect URL
            custom_css: URL to a custom CSS file
            custom_js: URL to a custom JavaScript file
            custom_favicon: URL to a custom favicon
            custom_swagger_ui_version: The version of Swagger UI to use
            dom_id: The DOM element ID to bind to
            layout: The layout to use (BaseLayout, StandaloneLayout)
            plugins: The plugins to use
            presets: The presets to use
        """
        self.theme = theme
        self.deep_linking = deep_linking
        self.display_operation_id = display_operation_id
        self.default_models_expand_depth = default_models_expand_depth
        self.default_model_expand_depth = default_model_expand_depth
        self.default_model_rendering = default_model_rendering
        self.display_request_duration = display_request_duration
        self.doc_expansion = doc_expansion
        self.filter = filter
        self.max_displayed_tags = max_displayed_tags
        self.operations_sorter = operations_sorter
        self.show_extensions = show_extensions
        self.show_common_extensions = show_common_extensions
        self.tag_sorter = tag_sorter
        self.use_unicode_characters = use_unicode_characters
        self.persist_authorization = persist_authorization
        self.syntax_highlight = syntax_highlight
        self.oauth2_redirect_url = oauth2_redirect_url
        self.custom_css = custom_css
        self.custom_js = custom_js
        self.custom_favicon = custom_favicon
        self.custom_swagger_ui_version = custom_swagger_ui_version
        self.dom_id = dom_id
        self.layout = layout
        self.plugins = plugins or []
        self.presets = presets or ["SwaggerUIBundle.presets.apis", "SwaggerUIStandalonePreset"]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary.
        
        Returns:
            A dictionary with the configuration options.
        """
        config = {
            "theme": self.theme,
            "deepLinking": self.deep_linking,
            "displayOperationId": self.display_operation_id,
            "defaultModelsExpandDepth": self.default_models_expand_depth,
            "defaultModelExpandDepth": self.default_model_expand_depth,
            "defaultModelRendering": self.default_model_rendering,
            "displayRequestDuration": self.display_request_duration,
            "docExpansion": self.doc_expansion,
            "filter": self.filter,
            "showExtensions": self.show_extensions,
            "showCommonExtensions": self.show_common_extensions,
            "useUnicodeCharacters": self.use_unicode_characters,
            "persistAuthorization": self.persist_authorization,
            "dom_id": self.dom_id,
            "layout": self.layout,
        }
        
        if self.max_displayed_tags is not None:
            config["maxDisplayedTags"] = self.max_displayed_tags
        
        if self.operations_sorter is not None:
            config["operationsSorter"] = self.operations_sorter
        
        if self.tag_sorter is not None:
            config["tagSorter"] = self.tag_sorter
        
        if self.oauth2_redirect_url is not None:
            config["oauth2RedirectUrl"] = self.oauth2_redirect_url
        
        if self.plugins:
            config["plugins"] = self.plugins
        
        if self.presets:
            config["presets"] = self.presets
        
        return config


class SwaggerUI:
    """
    Swagger UI for APIFromAnything.
    
    This class provides a Swagger UI integration for APIs created with the 
    APIFromAnything library, with extensive customization options.
    """
    
    def __init__(
        self,
        openapi_generator: OpenAPIGenerator,
        url_prefix: str = "/docs",
        config: Optional[SwaggerUIConfig] = None,
        assets_dir: Optional[str] = None,
        static_files_route: str = "/static",
    ):
        """
        Initialize the Swagger UI.
        
        Args:
            openapi_generator: The OpenAPI generator instance
            url_prefix: The URL prefix for the documentation
            config: The Swagger UI configuration
            assets_dir: Directory containing custom assets (CSS, JS, images)
            static_files_route: The route for static files
        """
        self.openapi_generator = openapi_generator
        self.url_prefix = url_prefix.rstrip("/")
        self.config = config or SwaggerUIConfig()
        self.assets_dir = assets_dir
        self.static_files_route = static_files_route
        
        # Set up templates
        self.templates_path = Path(__file__).parent / "templates"
        if not self.templates_path.exists():
            self.templates_path.mkdir(parents=True)
            self._create_default_templates()
        
        self.templates = Jinja2Templates(directory=str(self.templates_path))
    
    def _create_default_templates(self) -> None:
        """
        Create default templates if they don't exist.
        """
        # Create the main template
        with open(self.templates_path / "swagger_ui.html", "w") as f:
            f.write(self._get_default_template())
        
        # Create the CSS template
        with open(self.templates_path / "swagger_ui_custom.css", "w") as f:
            f.write(self._get_default_css())
    
    def _get_default_template(self) -> str:
        """
        Get the default HTML template.
        
        Returns:
            The default HTML template for Swagger UI.
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@{{ swagger_ui_version }}/swagger-ui.css">
    {% if theme %}
    <link rel="stylesheet" type="text/css" href="{{ static_url }}/themes/{{ theme }}.css">
    {% endif %}
    {% if custom_css %}
    <link rel="stylesheet" type="text/css" href="{{ custom_css }}">
    {% else %}
    <style>
        {% include "swagger_ui_custom.css" %}
    </style>
    {% endif %}
    {% if custom_favicon %}
    <link rel="icon" type="image/png" href="{{ custom_favicon }}">
    {% else %}
    <link rel="icon" type="image/png" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@{{ swagger_ui_version }}/favicon-32x32.png" sizes="32x32">
    {% endif %}
</head>
<body>
    <div id="swagger-ui"></div>
    
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@{{ swagger_ui_version }}/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@{{ swagger_ui_version }}/swagger-ui-standalone-preset.js"></script>
    {% if custom_js %}
    <script src="{{ custom_js }}"></script>
    {% endif %}
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "{{ openapi_url }}",
                dom_id: "{{ dom_id }}",
                presets: [
                    {% for preset in presets %}
                    {{ preset }}{% if not loop.last %},{% endif %}
                    {% endfor %}
                ],
                layout: "{{ layout }}",
                deepLinking: {{ deep_linking|tojson }},
                displayOperationId: {{ display_operation_id|tojson }},
                defaultModelsExpandDepth: {{ default_models_expand_depth }},
                defaultModelExpandDepth: {{ default_model_expand_depth }},
                defaultModelRendering: "{{ default_model_rendering }}",
                displayRequestDuration: {{ display_request_duration|tojson }},
                docExpansion: "{{ doc_expansion }}",
                filter: {{ filter|tojson }},
                {% if max_displayed_tags %}maxDisplayedTags: {{ max_displayed_tags }},{% endif %}
                {% if operations_sorter %}operationsSorter: "{{ operations_sorter }}",{% endif %}
                showExtensions: {{ show_extensions|tojson }},
                showCommonExtensions: {{ show_common_extensions|tojson }},
                {% if tag_sorter %}tagSorter: "{{ tag_sorter }}",{% endif %}
                useUnicodeCharacters: {{ use_unicode_characters|tojson }},
                persistAuthorization: {{ persist_authorization|tojson }},
                syntaxHighlight: {
                    theme: "{{ syntax_highlight }}"
                },
                {% if oauth2_redirect_url %}oauth2RedirectUrl: "{{ oauth2_redirect_url }}",{% endif %}
                {% if plugins %}
                plugins: [
                    {% for plugin in plugins %}
                    {{ plugin }}{% if not loop.last %},{% endif %}
                    {% endfor %}
                ],
                {% endif %}
                onComplete: function() {
                    // Custom event handlers can be added here
                    console.log("Swagger UI loaded");
                    
                    // Apply custom theming
                    applyCustomTheme();
                }
            });
            
            function applyCustomTheme() {
                // Apply additional custom styling if needed
                // This function can be extended to apply dynamic themes
            }
            
            window.ui = ui;
        };
    </script>
</body>
</html>
"""
    
    def _get_default_css(self) -> str:
        """
        Get the default custom CSS.
        
        Returns:
            The default custom CSS for Swagger UI.
        """
        return """/* Custom Swagger UI Styling */

/* Header customization */
.swagger-ui .topbar {
    background-color: #1a365d;
    padding: 15px 0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.swagger-ui .topbar .wrapper {
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 1460px;
    margin: 0 auto;
    padding: 0 20px;
}

.swagger-ui .topbar a {
    max-width: 340px;
    font-size: 1.5em;
    font-weight: 700;
    color: white;
    text-decoration: none;
}

.swagger-ui .topbar img {
    height: 40px;
    margin-right: 10px;
}

/* Info section styling */
.swagger-ui .info {
    margin: 30px 0;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.swagger-ui .info .title {
    font-size: 36px;
    font-weight: 600;
    color: #2c3e50;
    margin: 0 0 15px 0;
}

.swagger-ui .info .description {
    font-size: 16px;
    line-height: 1.6;
}

.swagger-ui .info hgroup.main {
    margin: 0 0 20px 0;
    display: flex;
    align-items: center;
}

.swagger-ui .info .version {
    font-size: 14px;
    background: #e9ecef;
    border-radius: 20px;
    padding: 4px 12px;
    margin-left: 15px;
    color: #495057;
}

/* Tag sections */
.swagger-ui .opblock-tag {
    font-size: 24px;
    margin: 20px 0 10px 0;
    padding: 15px;
    background: #f1f6ff;
    border-radius: 6px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
    transition: all 0.3s ease;
}

.swagger-ui .opblock-tag:hover {
    background: #e6f0ff;
}

/* Operation blocks */
.swagger-ui .opblock {
    margin: 0 0 15px 0;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    transition: all 0.3s ease;
}

.swagger-ui .opblock:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    transform: translateY(-2px);
}

.swagger-ui .opblock.opblock-get {
    background: rgba(97, 175, 254, 0.1);
    border-color: #61affe;
}

.swagger-ui .opblock.opblock-post {
    background: rgba(73, 204, 144, 0.1);
    border-color: #49cc90;
}

.swagger-ui .opblock.opblock-put {
    background: rgba(252, 161, 48, 0.1);
    border-color: #fca130;
}

.swagger-ui .opblock.opblock-delete {
    background: rgba(249, 62, 62, 0.1);
    border-color: #f93e3e;
}

.swagger-ui .opblock.opblock-patch {
    background: rgba(80, 227, 194, 0.1);
    border-color: #50e3c2;
}

/* Operation summaries */
.swagger-ui .opblock .opblock-summary {
    padding: 12px 20px;
}

.swagger-ui .opblock .opblock-summary-method {
    min-width: 80px;
    text-align: center;
    font-size: 14px;
    font-weight: 700;
    border-radius: 4px;
    text-shadow: 0 1px 0 rgba(0, 0, 0, 0.1);
}

.swagger-ui .opblock .opblock-summary-path {
    font-size: 16px;
    font-weight: 600;
    font-family: 'Roboto Mono', monospace;
}

/* Request and response sections */
.swagger-ui .opblock-section-header {
    background: #f8f9fa;
    padding: 12px 20px;
    border-radius: 4px 4px 0 0;
}

.swagger-ui .parameters-container {
    padding: 15px 20px;
}

.swagger-ui .parameter__name {
    font-weight: 600;
    font-size: 14px;
}

.swagger-ui .parameter__type {
    font-size: 12px;
    color: #6c757d;
}

/* Models section */
.swagger-ui .model-container {
    margin: 20px 0;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 6px;
}

.swagger-ui .model-title {
    font-size: 18px;
    font-weight: 600;
}

/* Buttons */
.swagger-ui .btn {
    border-radius: 4px;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 13px;
    padding: 8px 16px;
    transition: all 0.2s ease;
}

.swagger-ui .btn.execute {
    background-color: #4caf50;
    color: white;
    box-shadow: 0 2px 5px rgba(76, 175, 80, 0.3);
}

.swagger-ui .btn.execute:hover {
    background-color: #43a047;
    box-shadow: 0 4px 8px rgba(76, 175, 80, 0.4);
}

.swagger-ui .btn.cancel {
    background-color: #f44336;
    color: white;
    box-shadow: 0 2px 5px rgba(244, 67, 54, 0.3);
}

.swagger-ui .btn.cancel:hover {
    background-color: #e53935;
    box-shadow: 0 4px 8px rgba(244, 67, 54, 0.4);
}

/* Authorize button */
.swagger-ui .auth-wrapper .authorize {
    background-color: #651fff;
    color: white;
    border-color: #651fff;
    box-shadow: 0 2px 5px rgba(101, 31, 255, 0.3);
}

.swagger-ui .auth-wrapper .authorize:hover {
    background-color: #5a1fee;
    box-shadow: 0 4px 8px rgba(101, 31, 255, 0.4);
}

/* Response section */
.swagger-ui .responses-inner {
    padding: 15px 20px;
}

.swagger-ui .responses-inner h4 {
    font-size: 16px;
    font-weight: 600;
}

.swagger-ui table {
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.swagger-ui table thead tr th {
    background: #f1f6ff;
    color: #2c3e50;
    font-weight: 600;
    padding: 12px 15px;
    border: none;
}

.swagger-ui table tbody tr td {
    padding: 10px 15px;
    border-top: 1px solid #e9ecef;
}

/* Code blocks */
.swagger-ui .highlight-code {
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .swagger-ui .opblock .opblock-summary-method {
        min-width: 60px;
        font-size: 12px;
    }
    
    .swagger-ui .opblock .opblock-summary-path {
        font-size: 14px;
    }
    
    .swagger-ui .info .title {
        font-size: 28px;
    }
}

/* Theme-specific styling - will be extended with other theme options */
.theme-material .swagger-ui .opblock {
    border-radius: 0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
}

.theme-outline .swagger-ui .opblock {
    background: transparent;
    border: 2px solid;
}

.theme-flattop .swagger-ui .opblock {
    border-radius: 0;
    border-top-width: 4px;
}

.theme-muted .swagger-ui .opblock {
    opacity: 0.9;
}
"""
    
    def _create_theme_files(self) -> None:
        """
        Create CSS files for the different themes.
        """
        themes_dir = self.templates_path / "themes"
        if not themes_dir.exists():
            themes_dir.mkdir(parents=True)
        
        # Create theme files
        themes = {
            "material": self._get_material_theme(),
            "muted": self._get_muted_theme(),
            "outline": self._get_outline_theme(),
            "flattop": self._get_flattop_theme(),
        }
        
        for name, content in themes.items():
            with open(themes_dir / f"{name}.css", "w") as f:
                f.write(content)
    
    def _get_material_theme(self) -> str:
        """Get the Material theme CSS."""
        return """/* Material Theme for Swagger UI */
.swagger-ui .opblock {
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    transition: all 0.3s cubic-bezier(.25,.8,.25,1);
    border: none;
}

.swagger-ui .opblock:hover {
    box-shadow: 0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23);
}

.swagger-ui .opblock-tag {
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    border-bottom: none;
}

.swagger-ui .btn {
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
    text-transform: uppercase;
    transition: all 0.3s cubic-bezier(.25,.8,.25,1);
    border: none;
}

.swagger-ui .btn:hover {
    box-shadow: 0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23);
}

.swagger-ui select {
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    border: none;
    border-radius: 4px;
}

.swagger-ui input[type=text] {
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    border: none;
    border-radius: 4px;
    padding: 8px 12px;
}

.swagger-ui .table-container {
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
    border-radius: 4px;
    overflow: hidden;
}
"""
    
    def _get_muted_theme(self) -> str:
        """Get the Muted theme CSS."""
        return """/* Muted Theme for Swagger UI */
.swagger-ui, .swagger-ui .info .title, .swagger-ui .opblock-tag, .swagger-ui .opblock .opblock-summary-operation-id, 
.swagger-ui .opblock .opblock-summary-path, .swagger-ui .opblock .opblock-summary-description {
    color: #5c6873;
}

.swagger-ui .topbar {
    background-color: #546E7A;
}

.swagger-ui .info {
    background-color: #f9fafb;
}

.swagger-ui .opblock {
    opacity: 0.85;
    transition: opacity 0.3s ease;
    border: none;
    box-shadow: 0 1px 3px rgba(92, 104, 115, 0.1);
}

.swagger-ui .opblock:hover {
    opacity: 1;
}

.swagger-ui .opblock-tag {
    border-bottom: 1px solid #eceff1;
    background: transparent;
}

.swagger-ui .opblock.opblock-get {
    background-color: rgba(97, 175, 254, 0.05);
}

.swagger-ui .opblock.opblock-post {
    background-color: rgba(73, 204, 144, 0.05);
}

.swagger-ui .opblock.opblock-put {
    background-color: rgba(252, 161, 48, 0.05);
}

.swagger-ui .opblock.opblock-delete {
    background-color: rgba(249, 62, 62, 0.05);
}

.swagger-ui .btn {
    opacity: 0.85;
    transition: opacity 0.3s ease;
    border-radius: 3px;
}

.swagger-ui .btn:hover {
    opacity: 1;
}
"""
    
    def _get_outline_theme(self) -> str:
        """Get the Outline theme CSS."""
        return """/* Outline Theme for Swagger UI */
.swagger-ui .opblock {
    background: transparent;
    border: 2px solid;
}

.swagger-ui .opblock.opblock-get {
    border-color: #61affe;
    background-color: transparent;
}

.swagger-ui .opblock.opblock-post {
    border-color: #49cc90;
    background-color: transparent;
}

.swagger-ui .opblock.opblock-put {
    border-color: #fca130;
    background-color: transparent;
}

.swagger-ui .opblock.opblock-delete {
    border-color: #f93e3e;
    background-color: transparent;
}

.swagger-ui .opblock.opblock-patch {
    border-color: #50e3c2;
    background-color: transparent;
}

.swagger-ui .opblock .opblock-summary-method {
    border: 2px solid;
}

.swagger-ui .opblock-tag {
    border: 2px solid #e8ebee;
    background: transparent;
}

.swagger-ui .btn {
    border: 2px solid;
    background: transparent;
    color: inherit;
}

.swagger-ui .btn.execute {
    border-color: #4caf50;
    color: #4caf50;
}

.swagger-ui .btn.execute:hover {
    background-color: #4caf50;
    color: white;
}

.swagger-ui .btn.cancel {
    border-color: #f44336;
    color: #f44336;
}

.swagger-ui .btn.cancel:hover {
    background-color: #f44336;
    color: white;
}

.swagger-ui .auth-wrapper .authorize {
    border-color: #651fff;
    color: #651fff;
}

.swagger-ui .auth-wrapper .authorize:hover {
    background-color: #651fff;
    color: white;
}
"""
    
    def _get_flattop_theme(self) -> str:
        """Get the Flattop theme CSS."""
        return """/* Flattop Theme for Swagger UI */
.swagger-ui .opblock {
    border-radius: 0;
    border: none;
    border-top-width: 4px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.swagger-ui .opblock .opblock-summary {
    border-bottom: 1px solid #ebebeb;
}

.swagger-ui .opblock .opblock-summary-method {
    border-radius: 0;
}

.swagger-ui .opblock-tag {
    border-radius: 0;
    border-bottom: 4px solid #ebebeb;
    background: transparent;
}

.swagger-ui .btn {
    border-radius: 0;
    text-transform: uppercase;
    font-weight: bold;
    border: none;
}

.swagger-ui .parameter__name,
.swagger-ui .parameters-col_name {
    font-family: monospace;
}

.swagger-ui .topbar {
    border-bottom: 4px solid #1f1f1f;
}

.swagger-ui .info {
    border-radius: 0;
    border-bottom: 4px solid #ebebeb;
}

.swagger-ui table {
    border-radius: 0;
}

.swagger-ui .model-container {
    border-radius: 0;
}
"""
    
    def _setup_static_files(self) -> Optional[StaticFiles]:
        """
        Set up static files for Swagger UI.
        
        Returns:
            Static files mounted app if assets_dir is provided, None otherwise.
        """
        # Create theme files
        self._create_theme_files()
        
        # If assets_dir is provided, mount it
        if self.assets_dir:
            return StaticFiles(directory=self.assets_dir)
        
        return StaticFiles(directory=str(self.templates_path))
    
    def setup_routes(self) -> List[Route]:
        """
        Set up routes for Swagger UI.
        
        Returns:
            A list of routes for Swagger UI.
        """
        routes = []
        
        # Main Swagger UI route
        routes.append(
            Route(
                f"{self.url_prefix}",
                endpoint=self.swagger_ui_html,
                methods=["GET"],
                name="swagger_ui",
            )
        )
        
        # OpenAPI JSON route
        routes.append(
            Route(
                f"{self.url_prefix}/openapi.json",
                endpoint=self.openapi_json,
                methods=["GET"],
                name="openapi_json",
            )
        )
        
        # Mount static files if available
        static_files = self._setup_static_files()
        if static_files:
            routes.append(
                Route(
                    f"{self.static_files_route}{{path:path}}",
                    endpoint=static_files,
                    name="swagger_static",
                )
            )
        
        return routes
    
    async def swagger_ui_html(self, request):
        """
        Serve the Swagger UI HTML page.
        
        Args:
            request: The request object
            
        Returns:
            A response containing the Swagger UI HTML
        """
        config = self.config.to_dict()
        
        return self.templates.TemplateResponse(
            "swagger_ui.html", 
            {
                "request": request,
                "title": self.openapi_generator.config.title,
                "openapi_url": f"{self.url_prefix}/openapi.json",
                "swagger_ui_version": self.config.custom_swagger_ui_version,
                "static_url": self.static_files_route,
                "theme": self.config.theme if self.config.theme != "default" else None,
                "custom_css": self.config.custom_css,
                "custom_js": self.config.custom_js,
                "custom_favicon": self.config.custom_favicon,
                "dom_id": self.config.dom_id.strip("#"),
                "layout": self.config.layout,
                "deep_linking": self.config.deep_linking,
                "display_operation_id": self.config.display_operation_id,
                "default_models_expand_depth": self.config.default_models_expand_depth,
                "default_model_expand_depth": self.config.default_model_expand_depth,
                "default_model_rendering": self.config.default_model_rendering,
                "display_request_duration": self.config.display_request_duration,
                "doc_expansion": self.config.doc_expansion,
                "filter": self.config.filter,
                "max_displayed_tags": self.config.max_displayed_tags,
                "operations_sorter": self.config.operations_sorter,
                "show_extensions": self.config.show_extensions,
                "show_common_extensions": self.config.show_common_extensions,
                "tag_sorter": self.config.tag_sorter,
                "use_unicode_characters": self.config.use_unicode_characters,
                "persist_authorization": self.config.persist_authorization,
                "syntax_highlight": self.config.syntax_highlight,
                "oauth2_redirect_url": self.config.oauth2_redirect_url,
                "plugins": self.config.plugins,
                "presets": self.config.presets,
            }
        )
    
    async def openapi_json(self, request):
        """
        Serve the OpenAPI JSON.
        
        Args:
            request: The request object.
            
        Returns:
            JSON response with the OpenAPI specification.
        """
        openapi_spec = self.openapi_generator.generate()
        
        # Add server information if not present
        if "servers" not in openapi_spec:
            base_url = str(request.base_url).rstrip("/")
            openapi_spec["servers"] = [{"url": base_url}]
        
        return JSONResponse(openapi_spec)
