from flask_restful import Resource
from flask import g, request
from marshmallow import ValidationError

from app.schemas.report import transaction_report_schema
from app.services.report import generate_transaction_report
from app.utils.permissions import authenticated_user
from app.utils.logger import logger


class TransactionReportResource(Resource):
    """Resource for generating transaction reports"""

    @authenticated_user()
    def get(self):
        """Generate a transaction report with date range filtering"""
        try:
            user = g.user
            # Get query parameters for filtering
            query_params = {
                "start_date": request.args.get("start_date"),
                "end_date": request.args.get("end_date"),
                "user_id": request.args.get("user_id"),
            }

            logger.info(
                f"User {user.id} requested transaction report with params: {query_params}"
            )

            report_data = generate_transaction_report(user, query_params)

            return report_data, 200

        except ValidationError as err:
            logger.warning(f"Validation error in report generation: {str(err)}")
            return {"error": str(err)}, 400
