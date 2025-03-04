# app/services/auth.py
import uuid, os
import re
from flask import url_for
from flask_mail import Message
from marshmallow.exceptions import ValidationError
from app.extensions import db, bcrypt, redis_client, mail
from app.models.user import User
from app.utils.logger import logger
from app.utils.tokens import TokenHandler
from app.tasks.auth import send_verification_email, send_password_reset_email
from app.utils.constants import (
    ACCCOUNT_VERIFICATION_LINK_SEND_RATE_LIMIT,
    ACCCOUNT_VERIFICATION_LINK_VALIDITY,
)


def create_user(user):
    """Create a new user and save to database."""

    user.set_password(user.password)
    db.session.add(user)
    db.session.commit()
    logger.info(f"User created successfully: {user}")
    return user


def send_account_verification_link(user, endpoint="auth.verify-user"):
    """
    Generate UUID token, store in Redis, and send email.
    Rate limited to prevent spam - only one link every 10 minutes per user.
    """
    # Check if a rate limit key exists for this user
    rate_limit_key = f"verify_rate_limit:{user.id}"

    # Check if user has requested a link in the past 10 minutes
    if redis_client.exists(rate_limit_key):
        time_remaining = redis_client.ttl(rate_limit_key)
        minutes_remaining = int(time_remaining / 60) + 1  # Round up to next minute

        logger.warning(f"Rate limit hit for verification email to {user.email}")
        raise ValidationError(
            f"Please wait {minutes_remaining} minutes before requesting another verification link"
        )

    # Generate verification token
    token = str(uuid.uuid4())
    redis_key = f"verification_token:{token}"

    verification_ttl = ACCCOUNT_VERIFICATION_LINK_VALIDITY
    rate_limit_ttl = ACCCOUNT_VERIFICATION_LINK_SEND_RATE_LIMIT

    redis_client.setex(
        redis_key, verification_ttl, str(user.id)
    )  # Token expires in 10 minutes

    # Set rate limit for 10 minutes (600 seconds)
    redis_client.setex(rate_limit_key, rate_limit_ttl, "1")

    logger.info(f"Stored token in Redis: {redis_key} -> {user.id}")

    verify_url = url_for(endpoint, token=token, _external=True)

    send_verification_email.delay(user.email, verify_url)
    logger.info(f"Account verification email sent to: {user.email}")
    return token


def verify_user_by_token(token):
    """Verify user using Redis-stored token."""

    redis_key = f"verification_token:{token}"
    user_id = redis_client.get(redis_key)
    if not user_id:
        logger.warning(f"Invalid or expired token: {token}")
        raise ValidationError("Invalid or expired verification token")

    user = User.query.get(uuid.UUID(user_id))
    if not user:
        logger.warning(f"No user found for token: {token}")
        raise ValidationError("User not found")
    if user.is_verified:
        logger.info(f"User already verified: {user.email}")
        redis_client.delete(redis_key)  # Clean up
        return False

    user.is_verified = True
    db.session.commit()
    redis_client.delete(redis_key)  # Clean up after verification
    logger.info(f"User verified: {user.email}")
    return True


def resend_account_verification_link(email):
    """Resend verification link for an existing, unverified user."""
    user = User.query.filter_by(email=email).first()
    if not user:
        logger.warning(f"No user found with email: {email}")
        raise ValidationError("Email not registered")
    if user.is_verified:
        logger.info(f"User already verified: {email}")
        raise ValidationError("User is already verified")

    # Generate and send new verification link
    token = send_account_verification_link(user)
    logger.info(f"Resent verification email to: {email}")
    return token


def is_email(login_str):
    """Check if string is an email format."""
    # Simple regex for basic email validation
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(email_regex, login_str) is not None


def authenticate_user(login_identifier, password):
    """
    Authenticate a user by username or email and password.
    """
    # Determine if the login identifier is an email or username
    if is_email(login_identifier):
        user = User.query.filter_by(email=login_identifier, is_deleted=False).first()
        identifier_type = "email"
    else:
        user = User.query.filter_by(username=login_identifier, is_deleted=False).first()
        identifier_type = "username"

    if not user:
        logger.warning(
            f"Login attempt with non-existent {identifier_type}: {login_identifier}"
        )
        raise ValidationError("Invalid username/email or password")

    if not user.is_verified:
        logger.warning(f"Login attempt with unverified account: {login_identifier}")
        raise ValidationError("Please verify your email before logging in")

    if not user.check_password(password):
        logger.warning(f"Failed login attempt for user: {login_identifier}")
        raise ValidationError("Invalid username/email or password")

    logger.info(f"User authenticated successfully: {login_identifier}")
    return user


def generate_tokens(user):
    """Generate access and refresh tokens for a user."""

    access_token = TokenHandler.generate_access_token(user, True)
    refresh_token = TokenHandler.generate_refresh_token(user)

    logger.info(f"Generated tokens for user: {user.username}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def send_password_reset_link(email, endpoint="auth.reset-password-confirm"):
    """
    Send a password reset link to user's email.
    """
    user = User.query.filter_by(email=email, is_deleted=False).first()

    # Check if a reset email was recently sent (rate limit)
    rate_limit_key = f"password_reset_link_rate_limit:{user.id}"
    if redis_client.exists(rate_limit_key):
        time_remaining = redis_client.ttl(rate_limit_key)
        minutes_remaining = int(time_remaining / 60)

        logger.warning(f"Rate limit hit for password reset email to {email}")
        raise ValidationError(
            f"Please wait {minutes_remaining} minutes before requesting another reset link"
        )

    # Generate reset token
    token = TokenHandler.generate_password_reset_token()
    TokenHandler.store_reset_token(user.id, token)

    # Generate reset URL
    reset_url = url_for(endpoint, token=token, _external=True)

    send_password_reset_email.delay(email, reset_url)

    logger.info(f"Password reset email sent to: {email} with token: {token}")
    return True


def reset_password_with_token(token, new_password):
    """
    Reset a user's password using a valid reset token.
    """
    user_id = TokenHandler.verify_reset_token(token)
    if not user_id:
        logger.warning(f"Invalid or expired password reset token")
        raise ValidationError("Invalid or expired reset token")

    try:
        user = User.query.get(uuid.UUID(user_id))
        if not user or user.is_deleted:
            logger.warning(f"User not found for reset token: {token}")
            raise ValidationError("User not found")

        # Update password
        user.set_password(new_password)
        db.session.commit()

        # Invalidate all existing tokens
        TokenHandler.invalidate_user_access_tokens(user.id)

        logger.info(f"Password reset successful for user: {user.email}")
        return user

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resetting password: {str(e)}", exc_info=True)
        raise ValidationError("An error occurred while resetting your password")
