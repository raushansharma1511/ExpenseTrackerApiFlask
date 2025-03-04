from marshmallow import (
    fields,
    validates,
    ValidationError,
    validates_schema,
    EXCLUDE,
    post_dump,
)
from marshmallow.validate import OneOf, Range
from marshmallow_enum import EnumField
from flask import g
from sqlalchemy import func
from datetime import datetime
import uuid

from app.extensions import ma, db
from app.models.transaction import Transaction, TransactionType
from app.models.category import Category
from app.models.user import User
from app.utils.logger import logger
from app.utils.constants import AMOUNT_MIN_VALUE as min_val, AMOUNT_MAX_VALUE as max_val


class TransactionSchema(ma.SQLAlchemyAutoSchema):
    """Schema for Transaction model - used for creation and reading"""

    class Meta:
        model = Transaction
        load_instance = True
        include_fk = True
        fields = (
            "id",
            "user_id",
            "type",
            "category_id",
            "amount",
            "date_time",
            "description",
            "is_deleted",
            "created_at",
            "updated_at",
        )
        dump_only = ("id", "is_deleted", "created_at", "updated_at")
        unknown = EXCLUDE

    type = EnumField(TransactionType, by_value=True)
    amount = fields.Float(required=True, validate=Range(min=min_val, max=max_val))

    @validates("user_id")
    def validate_user_id(self, value):
        """Validate user_id field"""
        logger.debug(f"Validating user_id: {value}")
        # Check if the user exists
        user = User.query.get(value)

        if not user or user.is_deleted:
            logger.warning(f"Validation failed: User not found for ID {value}")
            raise ValidationError("User not found")

        # Get current user for permission check
        current_user = g.user

        # Normal users can only create transactions for themselves
        if not current_user.is_staff:
            if str(value) != str(current_user.id):
                raise ValidationError("You can create transactions for yourself only")
        else:
            # Staff users can create transactions for normal users only
            if user.is_staff:
                raise ValidationError(
                    "Staff cannot create transactions for staff users"
                )

        logger.debug(f"User_id validation passed for ID {value}")
        return value

    @validates("category_id")
    def validate_category_id(self, value):
        """Validate category_id field"""
        logger.debug(f"Validating category_id: {value}")

        # Check if category exists and is not deleted
        category = Category.query.get(value)
        if not category or category.is_deleted:
            raise ValidationError("Category not found")

        logger.debug(f"Category_id validation passed for ID {value}")
        return value

    @validates_schema
    def validate_transaction(self, data, **kwargs):
        """Additional validation for the whole transaction"""
        logger.debug("Performing whole transaction validation")

        user_id = data["user_id"]
        category_id = data["category_id"]

        # Verify the category is available to this user
        # (either it's the user's own category or a predefined one)
        category = Category.query.get(category_id)

        if not category.is_predefined and str(category.user_id) != str(user_id):
            raise ValidationError(
                {"category_id": ["Category does not belong to the provided user."]}
            )

        logger.debug("Transaction validation passed")


class TransactionUpdateSchema(ma.SQLAlchemyAutoSchema):
    """Schema for updating Transaction - can't update user_id or type"""

    class Meta:
        model = Transaction
        load_instance = True
        include_fk = True
        fields = ("category_id", "amount", "date_time", "description")
        unknown = EXCLUDE

    # Field validations
    amount = fields.Float(required=True, validate=Range(min=min_val, max=max_val))

    @validates("category_id")
    def validate_category_id(self, value):
        """Validate category_id field"""
        logger.debug(f"Validating category_id for update: {value}")

        # Check if category exists and is not deleted
        category = Category.query.get(value)
        if not category or category.is_deleted:
            raise ValidationError("Category not found")

        # Get the instance being updated
        instance = self.instance

        # Verify the category is available to this user
        # (either it's the user's own category or a predefined one)
        if not category.is_predefined and str(category.user_id) != str(
            instance.user_id
        ):
            raise ValidationError("Category does not belong to the provided user.")

        logger.debug(f"Update category_id validation passed for ID {value}")
        return value


# Initialize schemas
transaction_schema = TransactionSchema()
transactions_schema = TransactionSchema(many=True)
transaction_update_schema = TransactionUpdateSchema()
