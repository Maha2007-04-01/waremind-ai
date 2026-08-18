import logging
from flask import Flask
from flask_cors import CORS
from config import Config
from database.db import init_db
from utils.helpers import error_response

# Import Route Blueprints
from routes.system_routes import system_bp
from routes.inventory_routes import inventory_bp
from routes.order_routes import order_bp
from routes.warehouse_routes import warehouse_bp
from routes.analytics_routes import analytics_bp
from routes.alert_routes import alert_bp
from routes.picking_routes import picking_bp
from routes.packing_routes import packing_bp
from routes.qc_routes import qc_bp
from routes.dispatch_routes import dispatch_bp
from routes.exception_routes import exception_bp
from routes.auth_routes import auth_bp
from routes.stockout_routes import stockout_bp
from routes.traceability_routes import traceability_bp
from routes.copilot_routes import copilot_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """
    Flask Application Factory
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure CORS for React frontend
    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})

    # Initialize SQLite Database Schema
    with app.app_context():
        init_db()

    # Register Blueprints
    app.register_blueprint(system_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(stockout_bp)
    app.register_blueprint(traceability_bp)
    app.register_blueprint(copilot_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(warehouse_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(picking_bp)
    app.register_blueprint(packing_bp)
    app.register_blueprint(qc_bp)
    app.register_blueprint(dispatch_bp)
    app.register_blueprint(exception_bp)


    # Centralized Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return error_response(message="Resource not found", status_code=404)

    @app.errorhandler(400)
    def handle_bad_request(e):
        return error_response(message="Bad request", status_code=400)

    @app.errorhandler(500)
    def handle_internal_error(e):
        logger.error(f"Internal Server Error: {str(e)}")
        return error_response(message="Internal server error", status_code=500)

    @app.errorhandler(Exception)
    def handle_unexpected_exception(e):
        logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)
        return error_response(message="An unexpected error occurred", status_code=500, details=str(e))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
