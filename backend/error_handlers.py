"""
Error Handlers
Centralized error handling for the application
"""

from flask import jsonify
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base class for API errors"""
    status_code = 400
    
    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv

class ValidationError(APIError):
    """Validation error"""
    status_code = 400

class AuthenticationError(APIError):
    """Authentication error"""
    status_code = 401

class AuthorizationError(APIError):
    """Authorization error"""
    status_code = 403

class NotFoundError(APIError):
    """Resource not found error"""
    status_code = 404

class ConflictError(APIError):
    """Resource conflict error"""
    status_code = 409

class ServerError(APIError):
    """Internal server error"""
    status_code = 500

def register_error_handlers(app):
    """Register error handlers with Flask app"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors"""
        logger.error(f"API Error: {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle bad request errors"""
        logger.error(f"Bad Request: {error}")
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle unauthorized errors"""
        logger.warning(f"Unauthorized access attempt: {error}")
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle forbidden errors"""
        logger.warning(f"Forbidden access attempt: {error}")
        return jsonify({'error': 'Forbidden', 'message': 'Insufficient permissions'}), 403
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle not found errors"""
        return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle internal server errors"""
        logger.error(f"Internal Server Error: {error}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle any unexpected errors"""
        logger.error(f"Unexpected Error: {error}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500
