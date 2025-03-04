import uuid
import secrets
import string
from marshmallow import ValidationError
from app.extensions import db, redis_client
from app.models.user import User
from app.utils.logger import logger
from app.tasks.user import send_email_change_otps
from app.utils.constants import (
    OTP_VALID_FOR,
    EMAIL_CHANGE_TOKEN_VALIDITY,
    EMAIL_CHANGE_TOKEN_RESEND,
)
from app.tasks.user import soft_delete_user_related_objects
from app.utils.tokens import TokenHandler


def request_email_change(user, new_email):
    """
    Request an email change with separate OTP verification for each email.
    """
    try:
        # Use the same redis_key for both OTPs and rate limiting
        redis_key = f"email_change:{user.id}"

        # Check if there's an existing pending email change request (rate limiting)
        if redis_client.exists(redis_key):
            time_remaining = redis_client.ttl(redis_key)
            minutes_remaining = int(time_remaining / 60) + 1
            raise ValidationError(
                f"Please wait {minutes_remaining} minutes before requesting another email change"
            )

        # Generate two different OTPs - 6 digit numeric codes
        current_email_otp = "".join(secrets.choice(string.digits) for _ in range(6))
        new_email_otp = "".join(secrets.choice(string.digits) for _ in range(6))

        # Store OTPs in Redis with expiration (eg. 15 minutes)
        redis_client.setex(
            redis_key, OTP_VALID_FOR, f"{new_email}:{current_email_otp}:{new_email_otp}"
        )

        # Send different OTPs to each email address asynchronously
        send_email_change_otps.delay(
            user.email, new_email, current_email_otp, new_email_otp
        )

        logger.info(
            f"Email change OTPs sent for user {user.id}: {user.email} -> {new_email}"
        )
        return True

    except ValidationError as e:
        # Pass through validation errors
        raise
    except Exception as e:
        logger.error(f"Error requesting email change: {str(e)}", exc_info=True)
        raise Exception(
            f"An error occurred while processing the email change request: {str(e)}"
        )


def confirm_email_change(user, current_email_otp, new_email_otp):
    """
    Confirm email change with separate OTPs for each email.

    Args:
        user: The user requesting the change
        current_email_otp: OTP sent to the current email
        new_email_otp: OTP sent to the new email

    Returns:
        bool: True if successful

    Raises:
        ValidationError: If verification fails
    """
    try:
        # Get stored data from Redis
        redis_key = f"email_change:{user.id}"
        stored_data = redis_client.get(redis_key)

        if not stored_data:
            raise ValidationError("Otp is expired")

        new_email, stored_current_otp, stored_new_otp = stored_data.split(":")

        if current_email_otp != stored_current_otp and new_email_otp != stored_new_otp:
            raise ValidationError("Both current and new email OTPs are incorrect.")

        if current_email_otp != stored_current_otp:
            raise ValidationError("Invalid current email otp")

        if new_email_otp != stored_new_otp:
            raise ValidationError("Invalid new email otp.")

        # Update email
        user.email = new_email
        db.session.commit()

        # Delete Redis key
        redis_client.delete(redis_key)

        logger.info(f"Email changed for user {user.id} to {new_email}")
        return True

    except ValidationError as e:
        # Pass through validation errors
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error confirming email change: {str(e)}", exc_info=True)
        raise Exception(f"Failed to change email: {str(e)}")


def generate_staff_email_change_token(user, new_email):
    """
    Generate a token for staff-initiated email change for a particular user and store in Redis.
    """
    # Generate a random token
    token = secrets.token_urlsafe(32)

    # Store in Redis with 24 hour expiration
    redis_key = f"staff_email_change:{token}"

    redis_ttl_key = f"staff_email_change_ttl:{user.id}"

    if redis_client.exists(redis_ttl_key):
        time_remaining = redis_client.ttl(redis_ttl_key)
        minutes_remaining = int(time_remaining / 60)
        raise ValidationError(
            f"Please wait {minutes_remaining} minutes before requesting another email change"
        )

    redis_client.setex(redis_ttl_key, EMAIL_CHANGE_TOKEN_RESEND, "1")
    redis_client.setex(redis_key, EMAIL_CHANGE_TOKEN_VALIDITY, f"{user.id}:{new_email}")

    logger.info(
        f"Staff-initiated email change token generated for user {user.id}: {user.email} -> {new_email}"
    )
    return token


def verify_staff_email_change_token(token):
    """
    Verify a staff-initiated email change token.
    Args:
        token: The verification token
    Returns:
        tuple: (user_id, new_email) if valid, (None, None) if invalid
    """
    redis_key = f"staff_email_change:{token}"
    stored_data = redis_client.get(redis_key)

    if not stored_data:
        return None, None

    # Delete the key to prevent reuse
    redis_client.delete(redis_key)

    # Parse the stored data

    user_id, new_email = stored_data.split(":")

    return user_id, new_email


def delete_user_account(current_user, target_user, password=None):
    """
    Delete a user account (soft delete) and its related things.
    """
    try:
        # Perform soft delete
        target_user.is_deleted = True
        db.session.commit()

        soft_delete_user_related_objects.delay(str(target_user.id))

        logger.info(
            f"User account deleted - ID: {target_user.id}, Email: {target_user.email}, "
            + f"Deleted by: {current_user.id}"
        )

        return True

    except ValidationError as e:
        # Pass through validation errors
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user account: {str(e)}", exc_info=True)
        raise Exception(f"Failed to delete user account: {str(e)}")
