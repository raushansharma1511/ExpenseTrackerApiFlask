from flask_restful import Resource
from flask import request, g
from marshmallow import ValidationError
from sqlalchemy import or_

from app.extensions import db
from app.models.category import Category
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.category import (
    category_schema,
    categories_schema,
    category_update_schema,
)
from app.services.category import get_user_categories
from app.utils.permissions import (
    authenticated_user,
    object_permission,
    category_permission,
)
from app.utils.responses import validation_error_response
from app.utils.pagination import paginate
from app.utils.validators import normalize_category_name
from app.utils.logger import logger


class CategoryListResource(Resource):
    """Resource for listing and creating categories"""

    method_decorators = [authenticated_user()]

    def get(self):
        """Get paginated list of categories"""
        # Get query parameters
        user = g.user
        query_params = {
            "user_id": request.args.get("user_id"),
        }

        query = get_user_categories(user, query_params)

        # Use pagination utility
        result = paginate(
            query=query, schema=categories_schema, endpoint="category.categories"
        )
        logger.info(f"category retrieved succesfully by user {user}")
        return result, 200

    def post(self):
        """Create a new category"""
        try:
            # Get data
            data = request.get_json() or {}
            logger.info(
                f"Category creation request received by user {g.user.id}: {data}"
            )

            # Validate and create category
            category = category_schema.load(data)

            # Save to database
            db.session.add(category)
            db.session.commit()
            logger.info(
                f"Category created successfully: {category.id} by user {g.user.id}"
            )

            return category_schema.dump(category), 201

        except ValidationError as err:
            return validation_error_response(err)


class CategoryDetailResource(Resource):
    """Resource for retrieving, updating and deleting a category"""

    method_decorators = [
        object_permission(
            Category, id_param="category_id", check_fn=category_permission
        ),
        authenticated_user(),
    ]

    def get(self, category_id):
        """Get a specific category"""
        # Object is already loaded by permission decorator
        category = g.object
        logger.info(
            f"Category {category.id} retrieved successfully by user {g.user.id}"
        )
        return category_schema.dump(category), 200

    def patch(self, category_id):
        """Update a specific category's name"""
        try:
            category = g.object  # Object is already loaded by permission decorator
            data = request.get_json() or {}

            logger.info(
                f"Category update request for {category.id} by user {g.user.id}: {data}"
            )

            # Update just the name using the update schema
            updated_category = category_update_schema.load(
                data, instance=category, partial=True
            )
            updated_category.name = normalize_category_name(updated_category.name)
            db.session.commit()

            logger.info(
                f"Category updated successfully: {updated_category.id} by user {g.user.id}"
            )
            return category_schema.dump(updated_category), 200

        except ValidationError as err:
            return validation_error_response(err)

    def delete(self, category_id):
        """Delete a specific category"""
        # Object is already loaded by permission decorator
        category = g.object

        # Perform check if category is used in transactions
        transactions_exist = (
            Transaction.query.filter(
                Transaction.category_id == category.id, Transaction.is_deleted == False
            ).first()
            is not None
        )
        if transactions_exist:
            logger.warning(
                f"Attempt to delete category {category.id} with existing transactions by user {g.user.id}"
            )
            return {
                "error": "This category cannot be deleted as there are associated transactions."
            }, 400

        # Soft delete the category
        category.is_deleted = True
        db.session.commit()

        logger.info(
            f"Category soft deleted successfully: {category.id} by user {g.user.id}"
        )
        return {"message": "Category deleted successfully"}, 200
