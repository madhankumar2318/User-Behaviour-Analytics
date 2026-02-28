"""
API Documentation Configuration
Swagger/OpenAPI documentation for all endpoints
"""

from flasgger import Swagger

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "User Behavior Analytics API",
        "description": "API for user behavior monitoring and risk assessment",
        "version": "1.0.0",
        "contact": {
            "name": "API Support",
            "email": "support@example.com"
        }
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
        }
    },
    "security": [{"Bearer": []}],
    "tags": [
        {
            "name": "Authentication",
            "description": "User authentication and session management"
        },
        {
            "name": "Users",
            "description": "User management operations (Admin only)"
        },
        {
            "name": "Activity Logs",
            "description": "User activity logging and retrieval"
        },
        {
            "name": "Audit",
            "description": "Audit log operations"
        },
        {
            "name": "ML",
            "description": "Machine learning model operations"
        }
    ]
}

def init_swagger(app):
    """Initialize Swagger documentation"""
    return Swagger(app, config=swagger_config, template=swagger_template)
