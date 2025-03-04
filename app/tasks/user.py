from app.extensions import mail, db
from app.utils.logger import logger
from app.celery_app import celery
from app.utils.constants import OTP_VALID_FOR, EMAIL_CHANGE_TOKEN_VALIDITY
from app.utils.tokens import TokenHandler
from app.models.user import User
from app.utils.email_helper import send_templated_email
from app.models.category import Category
from app.models.transaction import Transaction


@celery.task(name="send_email_change_otps", bind=True, max_retries=3)
def send_email_change_otps(
    self, current_email, new_email, current_email_otp, new_email_otp
):
    """
    Task to send different OTPs to current and new email addresses.
    """
    try:
        # Calculate expiry minutes
        expiry_minutes = int(OTP_VALID_FOR / 60)

        # Send OTP to current email
        send_templated_email(
            recipient=current_email,
            subject="Verify Your Email Change Request - Expense Tracker",
            template="emails/user/current_email_otp.html",
            otp=current_email_otp,
            expiry_minutes=expiry_minutes,
        )

        # Send different OTP to new email
        send_templated_email(
            recipient=new_email,
            subject="Verify Your New Email Address - Expense Tracker",
            template="emails/user/new_email_otp.html",
            otp=new_email_otp,
            expiry_minutes=expiry_minutes,
        )

        logger.info(f"Email change OTPs sent to {current_email} and {new_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email change OTPs: {str(e)}", exc_info=True)
        # Retry with exponential backoff
        retry_in = 60 * (2**self.request.retries)  # 60s, 120s, 240s
        raise self.retry(exc=e, countdown=retry_in)


@celery.task(name="send_staff_email_change_verification", bind=True, max_retries=3)
def send_staff_email_change_verification(self, new_email, verification_url, username):
    """
    Send verification email for staff-initiated email change.
    """
    try:
        # Calculate expiry hours
        expiry_hours = int(EMAIL_CHANGE_TOKEN_VALIDITY / 3600)

        send_templated_email(
            recipient=new_email,
            subject="Verify Your New Email Address - Expense Tracker",
            template="emails/user/staff_email_change.html",
            verification_url=verification_url,
            username=username,
            expiry_hours=expiry_hours,
        )

        logger.info(f"Email change verification sent to {new_email}")
        return True

    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}", exc_info=True)
        # Retry with exponential backoff
        retry_in = 60 * (2**self.request.retries)  # 60s, 120s, 240s
        raise self.retry(exc=e, countdown=retry_in)


@celery.task(name="delete_user_objects", bind=True, max_retries=3)
def soft_delete_user_related_objects(self, user_id):
    """
    Task to clean up related data after a user is soft-deleted.
    This performs any necessary archiving or cleanup operations.

    Args:
        user_id: UUID of the user that was deleted
    """
    try:
        logger.info(f"Starting cleanup for user {user_id}")
        TokenHandler.invalidate_user_access_tokens(user_id)

        categories_deleted = Category.query.filter_by(
            user_id=user_id, is_deleted=False
        ).update(
            {"is_deleted": True},
        )
        logger.info(f"Soft deleted {categories_deleted} categories for user {user_id}")

        # Soft delete all user's transactions
        transactions_deleted = Transaction.query.filter_by(
            user_id=user_id, is_deleted=False
        ).update(
            {"is_deleted": True},
        )
        logger.info(
            f"Soft deleted {transactions_deleted} transactions for user {user_id}"
        )

        db.session.commit()
        logger.info(f"Cleanup completed for user {user_id}")
        return True

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in user cleanup: {str(e)}", exc_info=True)
        # Retry with exponential backoff
        retry_in = 60 * (2**self.request.retries)  # 60s, 120s, 240s
        raise self.retry(exc=e, countdown=retry_in)
