from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import jsonify, request, g
from functools import wraps
from app.models.user import User
from app.models.auth import ActiveAccessToken
import uuid
from app.utils.logger import logger
from app.utils.validators import is_valid_uuid
from app.extensions import db


def authenticated_user():
    """
    Decorator to check if the user is authenticated and their token is in the database.
    Attaches the user to Flask's g object as g.user.
    """

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                logger.warning("Invalid authorization header: Missing 'Bearer ' prefix")
                return (
                    {
                        "error": "Invalid authorization header, must start with 'Bearer'."
                    },
                    401,
                )

            token = auth_header.split(" ")[1]
            token_entry = ActiveAccessToken.query.filter_by(access_token=token).first()
            if not token_entry:
                logger.error(
                    f"Authentication failed: Token '{token}' not found in ActiveAccessToken"
                )
                return (
                    {"error": "Invalid authorization detail."},
                    401,
                )

            user = token_entry.user
            if not user:
                logger.error(
                    f"Authentication failed: No user associated with token '{token}'"
                )
                return (
                    {
                        "error": "Invalid authorization detail.",
                    },
                    401,
                )

            g.user = user
            logger.info(f"User authenticated successfully: {user.id}")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def object_permission(model_class, id_param="id", check_fn=None):
    """
    Generic object permission decorator that retrieves an object and checks permissions.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            object_id = kwargs.get(id_param)
            if not object_id:
                logger.warning(f"Missing {id_param} in request")
                return {"error": "Missing object ID"}, 400

            try:
                object_id = uuid.UUID(object_id)
            except ValueError:
                logger.warning(f"Invalid {id_param} format: {object_id}")
                return {"error": f"Invalid {id_param} format"}, 400

            obj = model_class.query.get(object_id)
            if not obj:
                logger.error(f"{model_class.__name__} not found for ID: {object_id}")
                return {"error": f"{model_class.__name__} not found."}, 404

            request_user = g.user
            request_method = request.method

            if check_fn:
                has_permission = check_fn(request_user, obj, request_method)
            else:
                has_permission = False
                if request_method == "GET":
                    if request_user.is_staff:
                        has_permission = True
                    else:
                        if not obj.is_deleted and obj.user_id == request_user.id:
                            has_permission = True
                else:
                    has_permission = obj.is_deleted == False and (
                        request_user.is_staff or obj.user_id == request_user.id
                    )

            if not has_permission:
                logger.error(
                    f"Permission denied for user {request_user.id} on {model_class.__name__} {obj.id}"
                )
                return {"error": f"{model_class.__name__} not found"}, 404

            g.object = obj
            logger.info(
                f"Permission granted for user {request_user.id} on {model_class.__name__} {obj.id} ({request_method})"
            )
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def staff_required():
    """
    Decorator to ensure a user is authenticated and is staff.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not g.user.is_staff:
                logger.error(
                    f"Staff access denied for user {g.user.id}: Not a staff member"
                )
                return {
                    "error": "Permission denied",
                }, 403
            logger.info(f"Staff access granted for user {g.user.id}")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def user_profile_permission(user, obj, request_method):
    """
    Custom permission function for password updates.
    """
    if request_method == "GET":
        if user.is_staff:
            return True
        else:
            if not obj.is_deleted and obj.id == user.id:
                return True
        return False
    return not obj.is_deleted and (user.is_staff or obj.id == user.id)


def user_self_permission(user, obj, request_method):
    """Permissions for update password"""
    return user.id == obj.id


def user_email_change_permission(user, obj, request_method):
    """
    Custom permission function for email changes.
    """
    if user.id == obj.id:
        return True
    if user.is_staff:
        return True

    return False


def category_permission(user, obj, request_method):
    """
    Permission function for categories.
    """
    if request_method == "GET":
        if user.is_staff:
            return True
        else:
            return not obj.is_deleted and (obj.is_predefined or obj.user_id == user.id)
    else:
        if not obj.is_deleted:
            if user.is_staff:
                return True
            else:
                return obj.user_id == user.id
        return False
