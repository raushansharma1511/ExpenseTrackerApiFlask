from flask_restful import Resource
from flask import g, request
from marshmallow import ValidationError
from datetime import datetime

from app.extensions import db
from app.models.transaction import Transaction
from app.schemas.transaction import (
    transaction_schema,
    transactions_schema,
    transaction_update_schema,
)
from app.services.transaction import (
    get_user_transactions,
)
from app.utils.permissions import (
    authenticated_user,
    object_permission,
)
from app.utils.responses import validation_error_response
from app.utils.pagination import paginate
from app.utils.logger import logger


class TransactionListResource(Resource):
    """Resource for listing and creating transactions"""

    method_decorators = [authenticated_user()]

    def get(self):
        """Get paginated list of transactions with filtering"""
        user = g.user

        # Get query parameters for filtering
        query_params = {
            "type": request.args.get("type"),
            "from_date": request.args.get("from_date"),
            "to_date": request.args.get("to_date"),
            "category_id": request.args.get("category_id"),
            "user_id": request.args.get("user_id"),
        }
        logger.info(
            f"User {user.id} requested transactions list with filters: {query_params}"
        )
        # Get filtered query
        query = get_user_transactions(user, query_params)

        # Use pagination utility
        result = paginate(
            query=query, schema=transactions_schema, endpoint="transaction.transactions"
        )

        logger.info(
            f"Returned {result['pagination']['total_items']} transactions to user {user.id}"
        )
        return result, 200

    def post(self):
        """Create a new transaction"""
        try:
            # Get data

            data = request.get_json() or {}

            current_user = g.user

            logger.info(f"User {current_user.id} creating transaction: {data}")

            # Validate and create transaction
            transaction = transaction_schema.load(data)

            # Save to database
            db.session.add(transaction)
            db.session.commit()

            logger.info(
                f"Transaction created successfully with ID {transaction.id} by user {current_user.id}"
            )

            return transaction_schema.dump(transaction), 201

        except ValidationError as err:
            return validation_error_response(err)


class TransactionDetailResource(Resource):
    """Resource for retrieving, updating and deleting a transaction"""

    method_decorators = [
        object_permission(Transaction, id_param="transaction_id"),
        authenticated_user(),
    ]

    def get(self, transaction_id):
        """Get a specific transaction"""
        # Object is already loaded by permission decorator
        transaction = g.object

        logger.info(f"User {g.user.id} retrieved transaction {transaction_id}")

        return transaction_schema.dump(transaction), 200

    def patch(self, transaction_id):
        """Update a specific transaction"""
        try:
            # Object is already loaded by permission decorator
            transaction = g.object
            data = request.get_json() or {}

            logger.info(
                f"User {g.user.id} updating transaction {transaction_id}: {data}"
            )

            # Update using the update schema that prevents changing user_id and type
            updated_transaction = transaction_update_schema.load(
                data, instance=transaction, partial=True
            )
            db.session.commit()

            logger.info(
                f"Transaction {transaction_id} updated successfully by user {g.user.id}"
            )
            return transaction_schema.dump(updated_transaction), 200

        except ValidationError as err:
            return validation_error_response(err)

    def delete(self, transaction_id):
        """Delete a specific transaction"""

        # Object is already loaded by permission decorator
        transaction = g.object

        logger.info(f"User {g.user.id} deleting transaction {transaction_id}")

        # Soft delete the transaction
        transaction.is_deleted = True
        db.session.commit()

        logger.info(
            f"Transaction {transaction_id} deleted successfully by user {g.user.id}"
        )
        return {"message": "Transaction deleted successfully"}, 200
