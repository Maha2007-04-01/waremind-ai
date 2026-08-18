from flask import Blueprint
from ai.decision_engine import DecisionEngine
from utils.helpers import success_response, error_response
from database.db import get_db_connection

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/summary', methods=['GET'])
def get_summary():
    """GET /api/analytics/summary — Overall warehouse analytics summary."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM orders;")
        total_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'COMPLETED' OR status = 'DISPATCHED';")
        completed_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM exceptions WHERE status != 'RESOLVED';")
        active_alerts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM warehouse_tasks WHERE status IN ('PENDING', 'IN_PROGRESS');")
        active_tasks = cursor.fetchone()[0]

        conn.close()

        summary_data = {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "active_alerts": active_alerts,
            "active_tasks": active_tasks
        }
        return success_response(data=summary_data)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@analytics_bp.route('/decision-insights', methods=['GET'])
def get_decision_insights():
    """
    GET /api/analytics/decision-insights
    Proactive AI Decision Intelligence API.
    Returns Inventory Risks, Order Risks, Warehouse Bottlenecks, and Smart Actionable Recommendations.
    """
    try:
        insights = DecisionEngine.generate_decision_insights()
        return success_response(data=insights)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@analytics_bp.route('/audit-logs', methods=['GET'])
def get_audit_logs():
    """GET /api/analytics/audit-logs — Returns recent audit log activity."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 20;")
        logs = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return success_response(data=logs)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

