from datetime import datetime, timezone
from app.extensions import db
from app.models.base import BaseModel
from app.utils.constants import TransactionType


class Transaction(BaseModel):
    """Transaction model to store financial transactions"""

    __tablename__ = "transactions"

    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type = db.Column(
        db.Enum(TransactionType),
        nullable=False,
    )
    category_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date_time = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    description = db.Column(db.Text, nullable=True)

    # Define relationships
    user = db.relationship(
        "User", backref=db.backref("transactions", lazy=True, cascade="all, delete")
    )
    category = db.relationship(
        "Category", backref=db.backref("transactions", lazy=True, cascade="all, delete")
    )

    def __repr__(self):
        return f"<Transaction {self.user.username} - {self.type.value} - {self.amount}>"
