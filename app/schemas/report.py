from marshmallow import Schema, fields
from app.models.transaction import Transaction


class TransactionReportSchema(Schema):
    category_name = fields.String(attribute="category.name", dump_only=True)
    amount = fields.Float(dump_only=True, as_string=True, precision=2)
    date_time = fields.DateTime(format="%Y-%m-%dT%H:%M", dump_only=True)


transaction_report_schema = TransactionReportSchema(many=True)
