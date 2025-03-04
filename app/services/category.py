from app.models.category import Category
from app.models.user import User
from app.utils.logger import logger
from app.utils.validators import is_valid_uuid
from marshmallow import ValidationError
from sqlalchemy import or_, func
from flask import g


def get_user_categories(user, query_params=None):
    """
    Get categories for a user with optional filters

    Args:
        user: The user requesting categories
        query_params: Dict with optional filters (user_id, is_predefined)

    Returns:
        SQLAlchemy query object with appropriate filters
    """
    logger.info(f"Getting categories for user {user.id} with filters: {query_params}")

    # Initialize query
    query_params = query_params or {}

    # Start with base query depending on user type
    if user.is_staff:
        # Staff can see all categories
        logger.debug(f"User {user.id} is staff, retrieving all categories")
        query = Category.query

        # If specific user_id is provided and user is staff, filter by that
        if "user_id" in query_params and query_params["user_id"]:
            user_id = query_params["user_id"]

            if is_valid_uuid(user_id):
                logger.debug(f"Filtering categories by user_id: {user_id}")
                query = query.filter(Category.user_id == user_id)
            else:
                logger.warning(f"Invalid user_id format in request: {user_id}")
                raise ValidationError(f"Invalid user_id format: {user_id}")
    else:
        # Normal users can see predefined and their own categories
        logger.debug(
            f"User {user.id} is not staff, retrieving predefined and own categories"
        )
        query = Category.query.filter(
            Category.is_deleted == False,
            or_(Category.is_predefined == True, Category.user_id == user.id),
        )

    # Order by creation date for consistency
    query = query.order_by(Category.created_at)

    logger.debug("Category query built successfully")
    return query
