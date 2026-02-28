"""
Input Validation Schemas
Defines validation schemas for API requests using Marshmallow
"""

from marshmallow import Schema, fields, validate, ValidationError

class LoginSchema(Schema):
    """Schema for login requests"""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    password = fields.Str(required=True, validate=validate.Length(min=6))

class CreateUserSchema(Schema):
    """Schema for creating new users"""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    role = fields.Str(validate=validate.OneOf(['Admin', 'Analyst', 'Viewer']))
    full_name = fields.Str(validate=validate.Length(max=100))

class UpdateUserSchema(Schema):
    """Schema for updating users"""
    email = fields.Email()
    role = fields.Str(validate=validate.OneOf(['Admin', 'Analyst', 'Viewer']))
    full_name = fields.Str(validate=validate.Length(max=100))
    is_active = fields.Bool()

class ChangePasswordSchema(Schema):
    """Schema for password change"""
    old_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8))

class ResetPasswordSchema(Schema):
    """Schema for password reset"""
    new_password = fields.Str(required=True, validate=validate.Length(min=8))

class LogActivitySchema(Schema):
    """Schema for logging user activity"""
    user_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    login_time = fields.Str(required=True)
    location = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    downloads = fields.Int(required=True, validate=validate.Range(min=0, max=10000))
    failed_attempts = fields.Int(required=True, validate=validate.Range(min=0, max=100))
    ip_address = fields.Str(validate=validate.Length(max=45))  # IPv6 max length
    device_fingerprint = fields.Str(validate=validate.Length(max=200))

def validate_request(schema_class):
    """
    Decorator to validate request data against a schema
    Usage: @validate_request(LoginSchema)
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            schema = schema_class()
            try:
                # Validate and deserialize input
                validated_data = schema.load(request.json or {})
                # Add validated data to request for use in endpoint
                request.validated_data = validated_data
                return f(*args, **kwargs)
            except ValidationError as err:
                return jsonify({
                    'error': 'Validation failed',
                    'messages': err.messages
                }), 400
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
