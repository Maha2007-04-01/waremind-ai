from flask import Blueprint, jsonify
from database.db import get_db_connection
from utils.helpers import success_response, error_response

warehouse_bp = Blueprint('warehouse', __name__, url_prefix='/api/warehouse')

@warehouse_bp.route('/layout', methods=['GET'])
def get_layout():
    """GET /api/warehouse/layout — Get warehouse layout zones and locations."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM warehouse_locations ORDER BY zone, aisle, rack, bin;")
        rows = cursor.fetchall()
        conn.close()
        return success_response(data={"locations": [dict(r) for r in rows]})
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@warehouse_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """GET /api/warehouse/tasks — List all warehouse tasks."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.order_id, t.task_type, t.assigned_to, t.status, t.priority, 
                   t.started_at, t.completed_at, t.created_at,
                   o.order_number, o.customer_name
            FROM warehouse_tasks t
            LEFT JOIN orders o ON t.order_id = o.id
            ORDER BY t.created_at DESC;
        """)
        rows = cursor.fetchall()
        conn.close()
        return success_response(data=[dict(r) for r in rows])
    except Exception as e:
        return error_response(message=str(e), status_code=500)
