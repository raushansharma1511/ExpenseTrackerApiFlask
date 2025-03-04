from app.urls.auth import auth_bp
from app.urls.user import user_bp
from app.urls.category import category_bp
from app.urls.transaction import transaction_bp
from app.urls.report import report_bp


def register_blueprints(app):
    """Registers all Flask Blueprints (URL routing)"""
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(category_bp, url_prefix="/api/categories")
    app.register_blueprint(transaction_bp, url_prefix="/api/transactions")
    app.register_blueprint(report_bp, url_prefix="/api/reports")
