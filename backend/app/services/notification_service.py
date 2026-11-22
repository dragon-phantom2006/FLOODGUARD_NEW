import os
import requests
from ..extensions import db
from ..models import Notification, User
from .. import socketio


def notify_user(user, title, message, severity, source="system", alert_id=None):
    n = Notification(
        user_id=user.id,
        title=title,
        message=message,
        severity=severity,
        source=source,
        alert_id=alert_id,
    )
    db.session.add(n)
    db.session.commit()
    socketio.emit("notification:new", n.public(), room=f"user:{user.id}")
    return n


def _distance_km(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, asin, sqrt

    radius = 6371
    p1, p2 = radians(lat1), radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    value = sin(delta_lat / 2) ** 2 + cos(p1) * cos(p2) * sin(delta_lon / 2) ** 2
    return 2 * radius * asin(sqrt(value))


def emit_nearby_sensor_status(status):
    """Push every level change (including a return to Normal) to nearby members."""
    if status.get("latitude") is None or status.get("longitude") is None:
        return 0

    users = User.query.filter(
        User.active.is_(True),
        User.latitude.isnot(None),
        User.longitude.isnot(None),
    ).all()
    count = 0
    for user in users:
        distance = _distance_km(
            user.latitude,
            user.longitude,
            status["latitude"],
            status["longitude"],
        )
        if distance <= user.alert_radius_km:
            socketio.emit("sensor:status", status, room=f"user:{user.id}")
            count += 1
    return count


def sms_if_configured(mobile, message):
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    frm = os.getenv("TWILIO_FROM_NUMBER")
    if not all([sid, token, frm]):
        return {"status": "not_configured"}
    try:
        response = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
            auth=(sid, token),
            data={"From": frm, "To": mobile, "Body": message},
            timeout=10,
        )
        response.raise_for_status()
        return {"status": "sent", "provider": "twilio", "sid": response.json().get("sid")}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def notify_nearby_users(alert):
    users = User.query.filter(
        User.active.is_(True),
        User.latitude.isnot(None),
        User.longitude.isnot(None),
    ).all()
    count = 0
    for user in users:
        distance = _distance_km(
            user.latitude,
            user.longitude,
            alert.latitude,
            alert.longitude,
        )
        if distance <= user.alert_radius_km:
            notify_user(user, alert.title, alert.message, alert.code, "sensor_alert", alert.id)
            count += 1
    return count
