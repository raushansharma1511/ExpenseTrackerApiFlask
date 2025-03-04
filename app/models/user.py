from app.extensions import db, bcrypt
from app.models.base import BaseModel
from app.utils.logger import logger


class User(BaseModel):
    """User model with all its detail"""

    __tablename__ = "users"

    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_staff = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """Hashes and sets the password."""
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")
        logger.info(f"Password set for user {self.email}")

    def check_password(self, password):
        """Checks the hashed password."""
        return bcrypt.check_password_hash(self.password, password)

    def __repr__(self):
        return f"<User {self.username} {self.email} {self.name}>"
