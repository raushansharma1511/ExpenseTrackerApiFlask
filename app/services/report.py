from sqlalchemy import func, case
from datetime import datetime, timezone
from marshmallow import ValidationError

from app.models.transaction import Transaction, TransactionType
from app.models.category import Category
from app.models.user import User
from app.utils.logger import logger
from app.utils.validators import is_valid_uuid
from app.schemas.report import transaction_report_schema


def parse_and_validate_dates(start_date, end_date):
    """
    Parse and validate start_date and end_date
    """
    if not start_date or not end_date:
        raise ValidationError("Both start_date and end_date are required")

    try:
        # Parse dates and ensure they are at the start/end of the day
        parsed_start = datetime.strptime(start_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        parsed_end = datetime.strptime(end_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
        )
        if parsed_start > parsed_end:
            raise ValidationError("Start date cannot be after end date")

        return parsed_start, parsed_end
    except ValueError:
        raise ValidationError("Invalid date format. Use YYYY-MM-DD")


def get_target_user(current_user, user_id=None):
    """
    Determine the target user for the report based on authentication and permissions.
    """
    # Non-staff users can only see their own data; user_id is ignored
    if not current_user.is_staff:
        return current_user

    # Staff users must provide a user_id
    if not user_id:
        raise ValidationError("Staff users must provide a user_id of a normal user")

    if not is_valid_uuid(user_id):
        raise ValidationError("Invalid user_id format")

    target_user = User.query.get(user_id)
    if not target_user:
        raise ValidationError("User not found")

    if target_user.is_staff:
        raise ValidationError(
            "Passed user is a staff user and no data exits on behalf of staff users."
        )

    return target_user


def fetch_transactions(user, start_date, end_date):
    """
    Retrieve transactions for a user within a date range
    """
    return Transaction.query.filter(
        Transaction.user_id == user.id,
        Transaction.is_deleted == False,
        Transaction.date_time.between(start_date, end_date),
    )


def calculate_totals(query, transaction_type):
    """
    Calculate total income or expenses from a transaction query
    """
    total = (
        query.filter(Transaction.type == transaction_type)
        .with_entities(func.coalesce(func.sum(Transaction.amount), 0))
        .scalar()
    )

    return float(total or 0)


def group_transactions_by_category(query):
    """
    Group transactions by category with credit and debit totals and no of transactions in each category
    """
    category_summary = (
        query.join(Category, Transaction.category_id == Category.id)
        .with_entities(
            Category.name.label("category_name"),
            # Use case expression for conditional aggregation of credits
            func.sum(
                case(
                    (Transaction.type == TransactionType.credit, Transaction.amount),
                    else_=0,
                )
            ).label("total_credit"),
            # Use case expression for conditional aggregation of debits
            func.sum(
                case(
                    (Transaction.type == TransactionType.debit, Transaction.amount),
                    else_=0,
                )
            ).label("total_debit"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .group_by(Category.name)
        .all()
    )
    result = []
    for summary in category_summary:
        # Only include categories that have transactions
        if summary.total_credit or summary.total_debit:
            result.append(
                {
                    "category_name": summary.category_name,
                    "total_credit": float(summary.total_credit or 0),
                    "total_debit": float(summary.total_debit or 0),
                    "transaction_count": summary.transaction_count,
                }
            )
    # Sort by total (credit + debit) descending
    result.sort(key=lambda x: (x["total_credit"] + x["total_debit"]), reverse=True)
    return result


def generate_transaction_report(current_user, query_params=None):
    """
    Generate a transaction report with summaries and listings within a specified date range.
    - Normal user will get their own transaction report
    - Staff user will get the transaction report of normal users(user_id must be passed in query params)
    """
    logger.info(
        f"Generating transaction report for user {current_user.id} with params: {query_params}"
    )

    # Initialize query params
    query_params = query_params or {}

    # Parse and validate dates
    start_date, end_date = parse_and_validate_dates(
        query_params.get("start_date"), query_params.get("end_date")
    )

    # Get the target user for the report
    target_user = get_target_user(current_user, query_params.get("user_id"))
    logger.info(
        f"Generating report for target user: {target_user.id} in date range: {start_date} to {end_date}"
    )

    # Get base transaction query
    base_query = fetch_transactions(target_user, start_date, end_date)

    # Calculate totals
    total_income = calculate_totals(base_query, TransactionType.credit)
    total_expense = calculate_totals(base_query, TransactionType.debit)

    # Group by category with credit and debit totals
    category_summary = group_transactions_by_category(base_query)

    # Get credit and debit transactions using schemas for formatting
    credit_transactions = (
        base_query.filter(Transaction.type == TransactionType.credit)
        .order_by(Transaction.date_time.desc())
        .all()
    )

    debit_transactions = (
        base_query.filter(Transaction.type == TransactionType.debit)
        .order_by(Transaction.date_time.desc())
        .all()
    )

    # Use the schema to serialize the transaction objects
    credit_trans_list = transaction_report_schema.dump(credit_transactions)
    debit_trans_list = transaction_report_schema.dump(debit_transactions)

    # Build the complete report
    report = {
        "total_income": total_income,
        "total_expense": total_expense,
        "category_wise_income_expense": category_summary,
        "transactions": {
            "credit_transactions": credit_trans_list,
            "debit_transactions": debit_trans_list,
        },
    }

    logger.info(f"Transaction report generated successfully for user {target_user.id}")
    return report
