import enum

# jwt tokens
JWT_ACCESS_TOKEN_EXPIRES = 60  # in minutes
JWT_REFRESH_TOKEN_EXPIRES = 30  # in days


PASSWORD_RESET_LINK_SEND_RATE_LIMIT = 600  # Rate limiting period in seconds
PASSWORD_RESET_LINK_VALIDITY = 900  # in seconds

ACCCOUNT_VERIFICATION_LINK_SEND_RATE_LIMIT = 600  # in seconds
ACCCOUNT_VERIFICATION_LINK_VALIDITY = 3600  # in seconds


OTP_VALID_FOR = 300  # in seconds
EMAIL_CHANGE_TOKEN_VALIDITY = 12 * 3600  # in seconds
EMAIL_CHANGE_TOKEN_RESEND = 600  # in seconds


# for categories
CATEGORY_NAME_MIN_LENGTH = 1
CATEGORY_NAME_MAX_LENGTH = 100


# for transactions
class TransactionType(enum.Enum):
    """Enum for transaction types"""

    credit = "credit"
    debit = "debit"


AMOUNT_MIN_VALUE = 1
AMOUNT_MAX_VALUE = 99999999.99

# Pagination defaults
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
