from flask_restful import Resource
from flask import request, g
from flask import url_for
from marshmallow import ValidationError
from app.extensions import db
from app.models.user import User
from app.models.auth import ActiveAccessToken
from app.schemas.user import (
    user_profile_schema,
    users_profile_schema,
    user_update_schema,
    email_change_request_schema,
    email_change_confirm_schema,
    user_deletion_schema,
    password_update_schema,
)
from app.services.user import (
    request_email_change,
    confirm_email_change,
    delete_user_account,
    generate_staff_email_change_token,
    verify_staff_email_change_token,
)
from app.utils.permissions import (
    authenticated_user,
    staff_required,
    object_permission,
    user_profile_permission,
    user_self_permission,
    user_email_change_permission,
)
from app.tasks.user import send_staff_email_change_verification
from app.utils.responses import validation_error_response
from app.utils.pagination import paginate
from app.utils.logger import logger
from app.utils.tokens import TokenHandler


class UserListResource(Resource):
    """Resource to list all users (staff only)"""

    @authenticated_user()
    @staff_required()
    def get(self):
        """Get paginated list of all users"""
        logger.info(f"Staff user {g.user} requested list of all users")

        query = User.query.filter_by(is_deleted=False).order_by(User.created_at.desc())

        # Use pagination utility
        logger.info(f"Returned list of all users to staff user {g.user}")
        result = paginate(
            query=query, schema=users_profile_schema, endpoint="user.users"
        )
        return result, 200


class UserDetailResource(Resource):
    """Resource for getting, updating and deleting user profiles"""

    method_decorators = [
        object_permission(User, id_param="user_id", check_fn=user_profile_permission),
        authenticated_user(),
    ]

    def get(self, user_id):
        """Get user details"""
        logger.info(
            f"User {g.user} requested to get the profile details of user {g.object}"
        )

        user = g.object
        logger.info(f"Returned profile details for user {g.user}")
        return user_profile_schema.dump(user), 200

    def patch(self, user_id):
        """Update user profile (username, name)"""
        try:
            # Get data and users
            print("this ")
            data = request.get_json() or {}

            print("helos")
            logger.info(
                f"User {g.user} requested to update the profile details of user {g.object} with data {data}"
            )
            user = g.object
            current_user = g.user

            # Load data directly into the existing user instance
            updated_user = user_update_schema.load(data, instance=user, partial=True)
            db.session.commit()

            logger.info(f"Profile details updated successfully for user {g.user}")
            return user_profile_schema.dump(updated_user), 200

        except ValidationError as e:
            return validation_error_response(e)

    def delete(self, user_id):
        """Soft delete user"""
        try:
            # Get request data and users
            data = request.get_json() or {}
            logger.info(f"User {g.user} requested to delete user {g.object}")

            current_user = g.user
            target_user = g.object

            # Set context for schema validation
            user_deletion_schema.context = {
                "current_user": current_user,
                "target_user": target_user,
            }
            # Validate request data
            validated_data = user_deletion_schema.load(data)
            # Delete the user account
            delete_user_account(current_user, target_user)

            return {"message": "User deleted successfully"}, 200
        except ValidationError as e:
            return validation_error_response(e)


class PasswordUpdateResource(Resource):
    """Resource for updating a user's password with user_id in URL
    - Only the user themselves can update their password
    """

    method_decorators = [
        object_permission(User, id_param="user_id", check_fn=user_self_permission),
        authenticated_user(),
    ]

    def post(self, user_id):
        try:
            # Get request data
            data = request.get_json() or {}
            logger.info(f"User {g.user} requested to update his account password")

            # g.object is set by object_permission
            target_user = g.object

            # Pass target_user to schema context for current_password validation
            password_update_schema.context = {"target_user": target_user}

            # Validate and load data using the schema
            validated_data = password_update_schema.load(data)

            # Get current token
            auth_header = request.headers.get("Authorization", "")
            current_token = (
                auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else None
            )

            # Update password
            target_user.set_password(validated_data["new_password"])
            db.session.commit()

            # Invalidate all tokens except current one
            if current_token:
                to_delete = (
                    ActiveAccessToken.query.filter_by(user_id=target_user.id)
                    .filter(ActiveAccessToken.access_token != current_token)
                    .all()
                )
                for token in to_delete:
                    db.session.delete(token)
                db.session.commit()

            logger.info(f"Password updated successfully for user: {target_user.email}")

            return {"message": "Password updated successfully"}, 200

        except ValidationError as err:
            logger.warning(f"Validation error: {err.messages}")
            return validation_error_response(err)


class UserEmailChangeResource(Resource):
    """Resource for email change requests with different workflows based on user type.
    1. Regular user changing own email or staff user changing own email -> OTP verification flow
    2. Staff user changing another user's email -> Token verification flow
    """

    method_decorators = [
        object_permission(
            User, id_param="user_id", check_fn=user_email_change_permission
        ),
        authenticated_user(),
    ]

    def post(self, user_id):
        try:
            data = request.get_json() or {}
            request_user = g.user
            target_user = g.object  # Already set by object_permission decorator
            logger.info(
                f"User {request_user.id} requesting email change for user {target_user.id} to {data.get('new_email', 'unknown')}"
            )
            # Validate request data
            email_change_request_schema.context = {"user": target_user}
            validated_data = email_change_request_schema.load(data)
            new_email = validated_data["new_email"]

            # CASE 1: User changing their own email (staff or regular)
            if str(request_user.id) == str(user_id):
                # Use the existing OTP flow for self email change
                request_email_change(target_user, new_email)
                return {
                    "message": "Enter the otps sent to your current and new email addresses"
                }, 200

            # CASE 2: Staff user changing another user's email
            # (We know it's a staff user because other users would be blocked by the permission decorator)
            # Generate verification token and send email link
            token = generate_staff_email_change_token(target_user, new_email)
            verification_url = url_for("user.verify-email", token=token, _external=True)

            # Send verification email to the new email address
            send_staff_email_change_verification.delay(
                new_email, verification_url, target_user.username
            )
            logger.info(
                f"Verification email sent to {new_email} for staff-initiated email change for user {target_user.id}"
            )
            return {
                "message": f"Verification link sent to {new_email}. User must click the link to confirm email change."
            }, 200

        except ValidationError as e:
            return validation_error_response(e)


class EmailChangeConfirmResource(Resource):
    """Resource for confirming email changes with separate OTPs"""

    method_decorators = [
        object_permission(User, id_param="user_id", check_fn=user_self_permission),
        authenticated_user(),
    ]

    def post(self, user_id):
        """
        Confirm email change with separate OTPs for each email.
        Using user_password_permission to ensure only the user themselves can confirm.
        """
        try:
            data = request.get_json() or {}
            target_user = g.object  # Set by the object_permission decorator

            # Validate OTPs
            validated_data = email_change_confirm_schema.load(data)

            # Confirm email change with both OTPs
            confirm_email_change(
                target_user,
                validated_data["current_email_otp"],
                validated_data["new_email_otp"],
            )
            logger.info(f"Email updated successfully for user {target_user}")
            return {"message": "Email address updated successfully"}, 200

        except ValidationError as e:
            return validation_error_response(e)


class EmailChangeVerifyTokenResource(Resource):
    """Resource for verifying email change token (staff-initiated flow)"""

    def get(self, token):
        """Verify email change token and update user email"""
        try:
            # Verify token and update email
            if not token:
                return {"error": "Token is missing"}, 400

            user_id, new_email = verify_staff_email_change_token(token)

            if not user_id or not new_email:
                return {"error": "Invalid or expired verification token"}, 400

            # Get the user
            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}, 404

            # Update the user's email
            user.email = new_email
            db.session.commit()

            logger.info(f"Email updated successfully for user {user} to {new_email}")
            return {"message": "Email address updated successfully"}, 200

        except Exception as e:
            logger.error(f"Error verifying email change token: {str(e)}", exc_info=True)
            return {"error": "Failed to verify email change", "details": str(e)}, 500
