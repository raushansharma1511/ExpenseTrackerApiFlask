import re
from marshmallow import fields, validates, ValidationError, EXCLUDE, validates_schema
from app.extensions import ma
from app.models.user import User
from app.utils.validators import validate_username, validate_password


class UserProfileSchema(ma.SQLAlchemyAutoSchema):
    """Schema for user profile data"""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "name",
            "is_staff",
            "is_verified",
            "is_deleted",
            "created_at",
            "updated_at",
        )
        dump_only = (
            "id",
            "is_staff",
            "is_verified",
            "is_deleted",
            "created_at",
            "updated_at",
        )


class UserUpdateSchema(ma.SQLAlchemyAutoSchema):
    """Base schema for user updates with validation"""

    class Meta:
        model = User
        fields = ("username", "name")
        include_fk = True
        load_instance = True
        unknown = EXCLUDE

    @validates("username")
    def validate_username(self, value):
        """Validate username is unique"""
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise ValidationError(
                "Username must contain only letters, numbers, underscores, dots, or hyphens."
            )
        if len(value) < 5 or len(value) > 120:
            raise ValidationError("Username length should be between 5 to 120")
        # Get current instance
        instance = getattr(self, "instance", None)

        # Skip validation if value is unchanged
        if instance and instance.username == value:
            return value

        # Check uniqueness
        user = User.query.filter_by(username=value).first()
        if user:
            raise ValidationError("Username already exists")
        return value


class PasswordUpdateSchema(ma.Schema):
    current_password = fields.String(required=True)
    new_password = fields.String(required=True, validate=validate_password)
    confirm_password = fields.String(required=True)

    @validates("current_password")
    def validate_current_password(self, value):
        """Validate that the current_password matches the target user's password"""
        # Access target_user from schema context
        target_user = self.context.get("target_user")
        if not target_user:
            raise ValidationError("User context not provided for validation")

        # Assuming User has a method like check_password
        if not target_user.check_password(value):
            raise ValidationError("Current password is incorrect")

    @validates_schema
    def validate_passwords(self, data, **kwargs):
        """Validate that new_password and confirm_password match"""
        if data.get("new_password") != data.get("confirm_password"):
            raise ValidationError("Passwords must match", "confirm_password")


class EmailChangeRequestSchema(ma.Schema):
    """Schema for requesting email change - simplified version without password"""

    new_email = fields.Email(required=True)

    @validates("new_email")
    def validate_new_email(self, value):
        # Check if email already exists
        existing = User.query.filter_by(email=value).first()
        if existing:
            raise ValidationError("Email already exists")

        # Check if it's different from current email
        user = self.context.get("user")
        if user and user.email == value:
            raise ValidationError("New email must be different from your current email")

        return value


class EmailChangeConfirmSchema(ma.Schema):
    """Schema for confirming email change with two OTPs"""

    current_email_otp = fields.String(required=True)
    new_email_otp = fields.String(required=True)


class UserDeletionSchema(ma.Schema):
    """Schema for user account deletion"""

    password = fields.String(required=False)

    @validates_schema
    def validate(self, data, **kwargs):
        """
        Validate that password is provided if required.
        Staff deleting other users don't need to provide a password.
        Users deleting their own account must provide their password.
        """
        # Get context data
        current_user = self.context.get("current_user")
        target_user = self.context.get("target_user")

        if not current_user or not target_user:
            raise ValidationError("Missing context data")

        is_staff = current_user.is_staff

        if not is_staff:
            password = data.get("password")
            if not password:
                raise ValidationError(
                    "Password is required to delete your account", "password"
                )

            # Verify the password
            if not current_user.check_password(password):
                raise ValidationError("Incorrect password", "password")

        return data


# Initialize schema
user_deletion_schema = UserDeletionSchema()
# Initialize schemas
user_profile_schema = UserProfileSchema()
users_profile_schema = UserProfileSchema(many=True)
user_update_schema = UserUpdateSchema()
password_update_schema = PasswordUpdateSchema()
email_change_request_schema = EmailChangeRequestSchema()
email_change_confirm_schema = EmailChangeConfirmSchema()
