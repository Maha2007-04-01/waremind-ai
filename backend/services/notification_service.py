class NotificationService:
    @staticmethod
    def send_alert(alert_type, message, severity="INFO"):
        return {"type": alert_type, "message": message, "severity": severity, "sent": True}
