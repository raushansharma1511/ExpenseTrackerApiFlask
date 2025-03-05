A comprehensive RESTful API for tracking personal expenses and managing financial transactions built with Flask.

## Table of Contents

- Introduction
- Features
- Technology Stack
- Project Structure
- API Documentation
  - Authentication API
  - User Management API
  - Category Management API
  - Transaction Management API
  - Report API
- Database Schema
- Background Tasks
- Error Handling

## Introduction

The Flask Expense Tracker API is a robust financial management system designed to help users track their income and expenses. It provides a complete backend solution with secure authentication, comprehensive transaction management, and advanced reporting features.

## Features

- **User Authentication**: Secure signup/login flow with JWT, email verification, and password reset
- **User Management**: Profile management, email change with verification, account deletion
- **Category Management**: Create, update, and manage expense/income categories
- **Transaction Management**: Track financial transactions with detailed information
- **Reporting**: Generate comprehensive financial reports with date filtering and category breakdown
- **Role-Based Access Control**: Different permissions for regular users and administrators
- **Email Notifications**: Beautiful HTML email templates for account actions
- **Background Processing**: Asynchronous task handling with Celery and Redis

## Technology Stack

- **Framework**: Flask with Flask-RESTful
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT (JSON Web Tokens) with Flask-JWT-Extended
- **Task Queue**: Celery with Redis as message broker
- **Email**: Flask-Mail with HTML templates
- **Data Validation**: Marshmallow schemas
- **Migrations**: Flask-Migrate with Alembic


## Project Structure

```
expense_tracker_api_flask/
├── app/
│   ├── __init__.py                # Flask application factory
│   ├── config.py                  # Configuration settings
│   ├── extensions.py              # Flask extensions (SQLAlchemy, JWT, etc.)
│   ├── celery_app.py              # Celery configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                # Base model with common fields
│   │   ├── auth.py                # Authentication models (ActiveAccessToken)
│   │   ├── user.py                # User model
│   │   ├── category.py            # Category model
│   │   └── transaction.py         # Transaction model
│   ├── resources/
│   │   ├── auth.py                # Authentication API endpoints
│   │   ├── user.py                # User management endpoints
│   │   ├── category.py            # Category management endpoints
│   │   ├── transaction.py         # Transaction management endpoints
│   │   └── report.py              # Report generation endpoints
│   ├── schemas/
│   │   ├── auth.py                # Authentication-related schemas
│   │   ├── user.py                # User-related schemas
│   │   ├── category.py            # Category-related schemas
│   │   ├── transaction.py         # Transaction-related schemas
│   │   └── report.py              # Report-related schemas
│   ├── services/
│   │   ├── auth.py                # Authentication business logic
│   │   ├── user.py                # User management business logic
│   │   ├── category.py            # Category management business logic
│   │   ├── transaction.py         # Transaction management business logic
│   │   └── report.py              # Report generation business logic
│   ├── tasks/
│   │   ├── auth.py                # Authentication-related async tasks
│   │   └── user.py                # User-related async tasks
│   ├── templates/
│   │   └── emails/
│   │       ├── base.html          # Base email template
│   │       ├── auth/
│   │       │   ├── verification.html     # Account verification email
│   │       │   └── password_reset.html   # Password reset email
│   │       └── user/
│   │           ├── current_email_otp.html        # Current email OTP
│   │           ├── new_email_otp.html            # New email OTP
│   │           └── staff_email_change.html       # Staff email change
│   ├── urls/
│   │   ├── __init__.py            # Blueprint registration
│   │   ├── auth.py                # Authentication routes
│   │   ├── user.py                # User management routes
│   │   ├── category.py            # Category management routes
│   │   ├── transaction.py         # Transaction management routes
│   │   └── report.py              # Report generation routes
│   └── utils/
│       ├── constants.py           # Application constants
│       ├── email_helper.py        # Email helper functions
│       ├── error_handlers.py      # Global error handlers
│       ├── exceptions.py          # Custom exception classes
│       ├── jwt_handlers.py        # JWT token handlers
│       ├── logger.py              # Logging configuration
│       ├── pagination.py          # Pagination utilities
│       ├── permissions.py         # Permission decorators
│       ├── responses.py           # Standardized API responses
│       ├── tokens.py              # Token generation and verification
│       └── validators.py          # Data validation utilities
├── migrations/                    # Database migrations managed by Flask-Migrate
│   ├── README
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── logs/                          # Application logs directory
│   └── app.log
├── .env                           # Environment variables (not in version control)
├── .gitignore                     # Git ignore file
├── README.md                      # Project documentation
├── celery_worker.py               # Celery worker entry point
├── requirements.txt               # Project dependencies
└── run.py                         # Application entry point
```


# API Documentation for Expense Tracker API

### Authentication API

#### Register a new user
Creates a new user account with the provided details. A verification email will be sent to complete registration.

**Permissions:** Public access (no authentication required)

**Endpoint:** `POST /api/auth/sign-up`

**Request body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "Secure123!",
  "name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "message": "User registered successfully. Please check your email to verify your account.",
  "user": {
    "id": "fc083d64-474b-4093-ba0b-f92ac2850305",
    "username": "john_doe",
    "email": "john@example.com",
    "name": "John Doe",
    "is_staff": false,
    "is_verified": false,
    "is_deleted": false,
    "created_at": "2025-03-04T15:23:12.453Z",
    "updated_at": "2025-03-04T15:23:12.453Z"
  }
}
```

#### Verify user account
Verifies a user's email address using the token sent to their email during registration.

**Permissions:** Public access (no authentication required)

**Endpoint:** `GET /api/auth/verify-user/{token}`

**Response (200 OK):**
```json
{
  "message": "Email verified successfully"
}
```

#### Resend verification link
Resends the account verification email if the original one expired or was lost.

**Permissions:** Public access (no authentication required)

**Endpoint:** `POST /api/auth/resend-verification-link`

**Request body:**
```json
{
  "email": "john@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Verification link resent successfully. Please check your email."
}
```

#### Login
Authenticates a user and returns JWT access and refresh tokens.

**Permissions:** Public access (no authentication required)

**Endpoint:** `POST /api/auth/login`

**Request body:**
```json
{
  "username_or_email": "john@example.com",
  "password": "Secure123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Rate limiting:** Maximum 5 failed attempts before cooldown period

#### Refresh token
Generates a new access token using a valid refresh token when the access token expires.

**Permissions:** Valid refresh token required

**Endpoint:** `POST /api/auth/refresh-token`

**Headers:**
```
Authorization: Bearer {refresh_token}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
}
```

#### Logout
Invalidates the current access token, preventing its further use.

**Permissions:** Authenticated user

**Endpoint:** `POST /api/auth/logout`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

#### Request password reset
Initiates the password reset process by sending a reset link to the user's email.

**Permissions:** Public access (no authentication required)

**Endpoint:** `POST /api/auth/reset-password`

**Request body:**
```json
{
  "email": "john@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Check your gmail inbox, you will receive a password reset link shortly."
}
```

**Rate limiting:** One request every 10 minutes per email address

#### Confirm password reset
Sets a new password using the token received in the password reset email.

**Permissions:** Valid password reset token required

**Endpoint:** `POST /api/auth/reset-password-confirm/{token}`

**Request body:**
```json
{
  "password": "NewSecure456!",
  "confirm_password": "NewSecure456!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password has been reset successfully"
}
```

### User Management API

#### Get all users
Retrieves a paginated list of all users in the system.

**Permissions:** Staff users only

**Endpoint:** `GET /api/users`

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "fc083d64-474b-4093-ba0b-f92ac2850305",
      "username": "john_doe",
      "email": "john@example.com",
      "name": "John Doe",
      "is_staff": false,
      "is_verified": true,
      "created_at": "2025-03-04T15:23:12.453Z"
    },
    {
      "id": "a8205200-3d9d-4055-86c8-239379f34826",
      "username": "jane_smith",
      "email": "jane@example.com",
      "name": "Jane Smith",
      "is_staff": false,
      "is_verified": true,
      "created_at": "2025-03-04T16:45:32.123Z"
    }
  ],
  "pagination": {
    "total_items": 2,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 10,
    "has_next": false,
    "has_prev": false
  }
}
```

#### Get current user profile
Retrieves the profile details of the authenticated user.

**Permissions:** Authenticated user

**Endpoint:** `GET /api/users/me`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": "fc083d64-474b-4093-ba0b-f92ac2850305",
  "username": "john_doe",
  "email": "john@example.com",
  "name": "John Doe",
  "is_staff": false,
  "is_verified": true,
  "created_at": "2025-03-04T15:23:12.453Z"
}
```

#### Get user profile by ID
Retrieves detailed information about a specific user.

**Permissions:** Owner of the account or staff user(see the account of any user)

**Endpoint:** `GET /api/users/{user_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": "fc083d64-474b-4093-ba0b-f92ac2850305",
  "username": "john_doe",
  "email": "john@example.com",
  "name": "John Doe",
  "is_staff": false,
  "is_verified": true,
  "created_at": "2025-03-04T15:23:12.453Z"
}
```

#### Update user profile
Updates a user's profile information (username, name).

**Permissions:** Owner of the account or staff user(but the only non deleted users).

**Endpoint:** `PATCH /api/users/{user_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request body:**
```json
{
  "username": "johnny_doe",
  "name": "Johnny Doe"
}
```

**Response (200 OK):**
```json
{
  "id": "fc083d64-474b-4093-ba0b-f92ac2850305",
  "username": "johnny_doe",
  "email": "john@example.com",
  "name": "Johnny Doe",
  "is_staff": false,
  "is_verified": true,
  "created_at": "2025-03-04T15:23:12.453Z"
}
```

#### Update password
Changes a user's password after verifying the current password.

**Permissions:** Owner of the account only

**Endpoint:** `POST /api/users/{user_id}/update-password`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request body:**
```json
{
  "current_password": "Secure123!",
  "new_password": "StrongerPassword456!",
  "confirm_password": "StrongerPassword456!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password updated successfully"
}
```

#### Request email change (self-initiated)
Initiates the email change process by sending verification codes to both current and new email addresses. This flow is used when users themselves request an email change.

**Permissions:** Owner of the account only

**Endpoint:** `POST /api/users/{user_id}/update-email`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request body:**
```json
{
  "new_email": "newemail@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Enter the otps sent to your current and new email addresses"
}
```

**Rate limiting:** One request every 5 minutes per user

#### Confirm email change (self-initiated)
Completes the self-initiated email change process by verifying OTPs from both current and new email addresses.

**Permissions:** Owner of the account only

**Endpoint:** `POST /api/users/{user_id}/update-email/confirm`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request body:**
```json
{
  "current_email_otp": "123456",
  "new_email_otp": "654321"
}
```

**Response (200 OK):**
```json
{
  "message": "Email address updated successfully"
}
```

#### Request email change (staff-initiated)
Initiates an admin-driven email change process by sending a verification link to the new email address. This flow is used when staff members change another user's email.

**Permissions:** Staff users only

**Endpoint:** `POST /api/users/{user_id}/update-email`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request body:**
```json
{
  "new_email": "newemail@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Verification link sent to newemail@example.com. User must click the link to confirm email change."
}
```

#### Verify email change (staff-initiated)
Confirms a staff-initiated email change by verifying the token sent to the new email address.

**Permissions:** Public access (no authentication required, but valid token needed)

**Endpoint:** `GET /api/users/verify-email/{token}`

**Response (200 OK):**
```json
{
  "message": "Email address updated successfully"
}
```

#### Delete user account
Soft deletes a user account and associated data (categories, transactions).

**Permissions:** 
- Owner of the account (requires password verification)
- Staff user(but the only non deleted users) (no password required)

**Endpoint:** `DELETE /api/users/{user_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request body (for non-staff deleting own account):**
```json
{
  "password": "StrongerPassword456!"
}
```

**Response (200 OK):**
```json
{
  "message": "User deleted successfully"
}
```

### Category Management API

#### Get categories
Retrieves a paginated list of categories.

**Permissions:** 
- Authenticated user sees their own categories and predefined categories(created by staff)
- Staff users can see all categories with optional user_id filter

**Endpoint:** `GET /api/categories`

**Query Parameters:**
- `user_id`: Filter by user (staff only)
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "c5d0b4f8-9e6d-4c3a-8b7f-1d2e3f4a5b6c",
      "name": "Groceries",
      "user_id": "fc083d64-474b-4093-ba0b-f92ac2850305",
      "is_predefined": false,
      "created_at": "2025-03-05T09:23:17.453Z"
    },
    {
      "id": "b4c3d2e1-f5e6-d7c8-b9a0-1d2e3f4a5b6c",
      "name": "Salary",
      "user_id": "fc083d64-474b-4093-ba0b-f92ac2850305",
      "is_predefined": true,
      "created_at": "2025-03-05T09:45:32.123Z"
    }
  ],
  "pagination": {
    "total_items": 2,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 10,
    "has_next": false,
    "has_prev": false
  }
}
```

#### Create category
Creates a new category.
Category created by staff user will be by defalut a predefined category and available for all users.

**Permissions:** 
- Authenticated user creates for themselves
- Staff user can create for any user

**Endpoint:** `POST /api/categories`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request body:**
```json
{
  "name": "Entertainment",
  "user_id": "fc083d64-474b-4093-ba0b-f92ac2850305"
}
```

**Response (201 Created):**
```json
{
  "id": "d6e7f8g9-h0i1-j2k3-l4m5-n6o7p8q9r0s1",
  "name": "Entertainment",
  "user_id": "fc083d64-474b-4093-ba0b-f92ac2850305",
  "is_predefined": false,
  "created_at": "2025-03-05T14:27:45.782Z"
}
```

#### Get category details
Retrieves detailed information about a specific category.

**Permissions:** Owner of the category or staff user

**Endpoint:** `GET /api/categories/{category_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": "c5d0b4f8-9e6d-4c3a-8b7f-1d2e3f4a5b6c",
  "name": "Groceries",
  "user_id": "fc083d64-474b-4093-ba0b-f92ac2850305",
  "is_predefined": false,
  "created_at": "2025-03-05T09:23:17.453Z"
}
```

#### Update category
Updates the name of an existing category.(user_id cannot be updated due to data conflicts.)

**Permissions:** Owner of the category or staff user(only non deleted categories)

**Endpoint:** `PATCH /api/categories/{category_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request body:**
```json
{
  "name": "Food & Groceries"
}
```

**Response (200 OK):**
```json
{
  "id": "c5d0b4f8-9e6d-4c3a-8b7f-1d2e3f4a5b6c",
  "name": "Food & Groceries",
  "user_id": "fc083d64-474b-4093-ba0b-f92ac2850305",
  "is_predefined": false,
  "created_at": "2025-03-05T09:23:17.453Z"
}
```

#### Delete category
Soft deletes a category.(But only if its associated resources like transactions does not exists.)

**Permissions:** Owner of the category or staff user

**Endpoint:** `DELETE /api/categories/{category_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "message": "Category deleted successfully"
}
```

### Transaction Management API

#### Get transactions
Retrieves a paginated list of financial transactions with optional filtering.

**Permissions:** 
- Authenticated user sees their own transactions
- Staff user can see all transactions with optional user_id filter

**Endpoint:** `GET /api/transactions`

**Query Parameters:**
- `type`: "credit" or "debit" (optional)
- `from_date`: ISO format date (optional)
- `to_date`: ISO format date (optional)
- `category_id`: UUID of category (optional)
- `user_id`: UUID of user (optional, staff only)
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "f1e2d3c4-b5a6-9876-5432-1fedcba09876",
      "user_id": "fc083d64-474b-4093-ba0b-f92ac2850305",
      "type": "debit",
      "category_id": "c5d0b4f8-9e6d-4c3a-8b7f-1d2e3f4a5b6c",
      "amount": 45.67,
      "date_time": "2025-03-05T13:45:32.123Z",
      "description": "Weekly grocery shopping",
      "created_at": "2025-03-05T13:47:22.453Z"
    },
    {
      "id": "a9b8c7d6-e5f4-3210-9876-5432fedc1a0b",
      "user_id": "fc083d64-474b-4093-ba0b-f92ac2850305",
      "type": "credit",
      "category_id": "b4c3d2e1-f5e6-d7c8-b9a0-1d2e3f4a5b6c",
      "amount": 3000.00,
      "date_time": "2025-03-01T09:00:00.000Z",
      "description": "Monthly salary",
      "created_at": "2025-03-01T09:12:42.123Z"
    }
  ],
  "pagination": {
    "total_items": 2,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 10,
    "has_next": false,
    "has_prev": false,
    "links": {
      "first": "http://localhost:5000/api/transactions?page=1&per_page=10",
      "last": "http://localhost:5000/api/transactions?page=1&per_page=10"
    }
  }
}
```

#### Create transaction
Records a new financial transaction (credit or debit) with category classification.

**Permissions:** 
- Authenticated user creates for themselves
- Staff user can create for any user(but not for any staff user.)

**Endpoint:** `POST /api/transactions`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request body:**
```json
{
  "user_id": "fc083d64-474b-4093-ba0b-f92ac2850305",
  "type": "debit",
  "category_id": "c5d0b4f8-9e6d-4c3a-8b7f-1d2e3f4a5b6c",
  "amount": 78.42,
  "date_time": "2025-03-06T14:30:00.000Z",
  "description": "Online shopping" #optional
}
```

**Response (201 Created):**
```json
{
  "id": "e1d2c3b4-a5f6-9876-5432-1fedcba98765",
  "user_id": "fc083d64-474b-4093-ba0b-f92ac2850305",
  "type": "debit",
  "category_id": "c5d0b4f8-9e6d-4c3a-8b7f-1d2e3f4a5b6c",
  "amount": 78.42,
  "date_time": "2025-03-06T14:30:00.000Z",
  "description": "Online shopping",
  "created_at": "2025-03-06T14:32:12.453Z"
}
```

#### Get transaction details
Retrieves detailed information about a specific transaction.

**Permissions:** Owner of the transaction or staff user

**Endpoint:** `GET /api/transactions/{transaction_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": "f1e2d3c4-b5a6-9876-5432-1fedcba09876",
  "user_id": "fc083d64-474b-4093-ba0b-f92ac2850305",
  "type": "debit",
  "category_id": "c5d0b4f8-9e6d-4c3a-8b7f-1d2e3f4a5b6c",
  "amount": 45.67,
  "date_time": "2025-03-05T13:45:32.123Z",
  "description": "Weekly grocery shopping",
  "created_at": "2025-03-05T13:47:22.453Z"
}
```

#### Update transaction
Updates the details of an existing transaction.

**Permissions:** Owner of the transaction or staff user(only the non deleted transactions.)

**Endpoint:** `PATCH /api/transactions/{transaction_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request body:**
```json
{
  "amount": 52.35,
  "description": "Weekly grocery shopping with extras"
}
```

**Response (200 OK):**
```json
{
  "id": "f1e2d3c4-b5a6-9876-5432-1fedcba09876",
  "user_id": "fc083d64-474b-4093-ba0b-f92ac2850305",
  "type": "debit",
  "category_id": "c5d0b4f8-9e6d-4c3a-8b7f-1d2e3f4a5b6c",
  "amount": 52.35,
  "date_time": "2025-03-05T13:45:32.123Z",
  "description": "Weekly grocery shopping with extras",
  "created_at": "2025-03-05T13:47:22.453Z"
}
```

#### Delete transaction
Soft deletes a transaction from the system.

**Permissions:** Owner of the transaction or staff user.(only the non deleted transactions)

**Endpoint:** `DELETE /api/transactions/{transaction_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "message": "Transaction deleted successfully"
}
```

### Report API

#### Generate transaction report
Creates a comprehensive financial report with summaries and transaction listings for a specified date range.

**Permissions:** 
- Authenticated user can generate reports for their own data
- Staff user can generate reports for any user with specified user_id

**Endpoint:** `GET /api/transaction-report`

**Query Parameters:**
- `start_date`: Date in YYYY-MM-DD format (required)
- `end_date`: Date in YYYY-MM-DD format (required)
- `user_id`: UUID of user (optional, required for staff users viewing other users' reports)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "total_income": 3000.00,
  "total_expense": 176.44,
  "category_wise_income_expense": [
    {
      "category_name": "Salary",
      "total_credit": 3000.00,
      "total_debit": 0.00,
      "transaction_count": 1
    },
    {
      "category_name": "Food & Groceries",
      "total_credit": 0.00,
      "total_debit": 98.02,
      "transaction_count": 2
    },
    {
      "category_name": "Entertainment",
      "total_credit": 0.00,
      "total_debit": 78.42,
      "transaction_count": 1
    }
  ],
  "transactions": {
    "credit_transactions": [
      {
        "category_name": "Salary",
        "amount": "3000.00",
        "date_time": "2025-03-01T09:00"
      }
    ],
    "debit_transactions": [
      {
        "category_name": "Entertainment",
        "amount": "78.42",
        "date_time": "2025-03-06T14:30"
      },
      {
        "category_name": "Food & Groceries",
        "amount": "52.35",
        "date_time": "2025-03-05T13:45"
      },
      {
        "category_name": "Food & Groceries",
        "amount": "45.67",
        "date_time": "2025-03-03T16:21"
      }
    ]
  }
}
```

## Database Schema

### Users Table
- `id`: UUID (primary key)
- `username`: String (unique)
- `email`: String (unique)
- `password`: String (hashed)
- `name`: String
- `is_staff`: Boolean
- `is_verified`: Boolean
- `is_deleted`: Boolean
- `created_at`: DateTime
- `updated_at`: DateTime

### Active Access Tokens Table
- `id`: UUID (primary key)
- `access_token`: String (unique)
- `user_id`: UUID (foreign key to users)
- `created_at`: DateTime

### Categories Table
- `id`: UUID (primary key)
- `name`: String
- `user_id`: UUID (foreign key to users)
- `is_predefined`: Boolean
- `is_deleted`: Boolean
- `created_at`: DateTime
- `updated_at`: DateTime

### Transactions Table
- `id`: UUID (primary key)
- `user_id`: UUID (foreign key to users)
- `type`: Enum ('credit', 'debit')
- `category_id`: UUID (foreign key to categories)
- `amount`: Numeric
- `date_time`: DateTime
- `description`: Text (nullable)
- `is_deleted`: Boolean
- `created_at`: DateTime
- `updated_at`: DateTime

## Background Tasks

The application uses Celery with Redis for handling asynchronous tasks:

1. **Email Sending**: All email communications are processed in the background
   - Account verification emails
   - Password reset links
   - Email change verification OTPs

2. **User Data Cleanup**: When a user is deleted, related data cleanup happens asynchronously
   - Invalidating all user tokens
   - Soft deleting user's categories
   - Soft deleting user's transactions

## Error Handling

The API implements comprehensive error handling:

- **Validation Errors**: Provides detailed field-level error messages
- **Authorization Errors**: Proper 401/403 responses for unauthorized access
- **Not Found Errors**: 404 responses for missing resources
- **Server Errors**: Graceful handling with appropriate logging
- **Redis Errors**: Specialized handling for cache/queue failures


© 2025 Expense Tracker API. All rights reserved.