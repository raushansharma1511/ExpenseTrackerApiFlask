from app.extensions import db
from app.models.transaction import Transaction, TransactionType
from app.models.category import Category
from app.models.user import User
from app.utils.logger import logger
from marshmallow import ValidationError
from sqlalchemy import or_, and_
from datetime import datetime, timedelta, timezone
from flask import g
from app.utils.validators import is_valid_uuid


def get_user_transactions(user, query_params=None):
    """
    Get transactions for a user with optional filters

    Args:
        user: The user requesting transactions
        query_params: Dict with optional filters (type, from_date, to_date, category_id)

    Returns:
        SQLAlchemy query object with appropriate filters
    """
    logger.info(f"Getting transactions for user {user.id} with filters: {query_params}")

    # Initialize query
    query_params = query_params or {}

    if user.is_staff:
        # Staff can see all transactions
        logger.debug(f"User {user.id} is staff, retrieving all transactions")
        query = Transaction.query

        # If specific user_id is provided, filter by that
        if "user_id" in query_params and query_params["user_id"]:

            user_id = query_params["user_id"]

            if is_valid_uuid(user_id):
                logger.debug(f"Filtering by user_id: {query_params["user_id"]}")
                query = query.filter(Transaction.user_id == user_id)
            else:
                raise ValidationError(f"Invalid user_id format: {user_id}")
    else:
        # Normal users can only see their own transactions
        logger.debug(f"User {user.id} is not staff, retrieving only their transactions")
        query = Transaction.query.filter(
            Transaction.is_deleted == False, Transaction.user_id == user.id
        )

    # Apply filters if provided
    if "type" in query_params and query_params["type"]:
        transaction_type = TransactionType(query_params["type"])
        if not transaction_type:
            raise ValidationError(f"Invalid transaction type: {query_params['type']}")
        logger.debug(f"Filtering by transaction type: {transaction_type.value}")
        query = query.filter(Transaction.type == transaction_type)

    if "category_id" in query_params and query_params["category_id"]:
        category_id = query_params["category_id"]

        if is_valid_uuid(category_id):
            logger.debug(f"Filtering by category_id: {query_params['category_id']}")
            query = query.filter(Transaction.category_id == category_id)
        else:
            raise ValidationError(f"Invalid category_id format {category_id}")

    # Date range filters
    if "from_date" in query_params and query_params["from_date"]:
        try:
            from_date = datetime.fromisoformat(
                query_params["from_date"].replace("Z", "+00:00")
            ).replace(tzinfo=timezone.utc)
            logger.debug(f"Filtering by from_date: {from_date}")
            query = query.filter(Transaction.date_time >= from_date)
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Invalid from_date format: {query_params['from_date']}, error: {e}"
            )
            raise ValidationError(
                f"Invalid from_date format: {query_params['from_date']}"
            )

    if "to_date" in query_params and query_params["to_date"]:
        try:
            to_date = datetime.fromisoformat(
                query_params["to_date"].replace("Z", "+00:00")
            ).replace(tzinfo=timezone.utc)
            # Set to end of the day (23:59:59 UTC)
            to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            logger.debug(f"Filtering by to_date: {to_date}")
            query = query.filter(Transaction.date_time <= to_date)
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Invalid to_date format: {query_params['to_date']}, error: {e}"
            )
            raise ValidationError(f"Invalid to_date format: {query_params['to_date']}")

    # Order by date_time descending (newest first)
    query = query.order_by(Transaction.date_time.desc())

    logger.debug("Transaction query built successfully")
    return query
