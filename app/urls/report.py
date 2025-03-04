from flask import Blueprint
from flask_restful import Api
from app.resources.report import TransactionReportResource

report_bp = Blueprint("report", __name__)
report_api = Api(report_bp)

# Register endpoints
report_api.add_resource(
    TransactionReportResource, "/transaction", endpoint="transaction-report"
)
