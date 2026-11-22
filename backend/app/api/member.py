from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from ..utils.auth import current_user, require_role
from ..models import Alert, SafeLocation, Notification, Sensor, Telemetry
from ..services.alert_engine import level_for, details
from ..services.notification_service import notify_user
from math import radians, sin, cos, asin, sqrt

bp = Blueprint("member", __name__)


def dist(a, b, c, d):
    radius = 6371
    p1, p2 = radians(a), radians(c)
    dp, dl = radians(c - a), radians(d - b)
    value = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * radius * asin(sqrt(value))


@bp.put("/member/profile/location")
@require_role("member")
def update_location():
    from ..extensions import db

    user = current_user()
    data = request.get_json() or {}
    try:
        user.latitude = float(data["latitude"])
        user.longitude = float(data["longitude"])
        user.alert_radius_km = float(data.get("alert_radius_km", user.alert_radius_km))
    except (KeyError, TypeError, ValueError):
        return {"error": "latitude and longitude must be numeric."}, 400
    db.session.commit()
    return {"user": user.public()}


@bp.get("/member/dashboard")
@require_role("member")
def dashboard():
    user = current_user()
    notes = Notification.query.filter_by(user_id=user.id).order_by(Notification.id.desc()).limit(20).all()
    return {"user": user.public(), "notifications": [note.public() for note in notes]}


@bp.get("/notifications")
@require_role("member")
def notifications():
    user = current_user()
    notes = Notification.query.filter_by(user_id=user.id).order_by(Notification.id.desc()).limit(100).all()
    return {"notifications": [note.public() for note in notes]}


@bp.post("/notifications/<int:nid>/read")
@require_role("member")
def mark_read(nid):
    user = current_user()
    note = Notification.query.filter_by(id=nid, user_id=user.id).first_or_404()
    note.read = True
    from ..extensions import db

    db.session.commit()
    return {"notification": note.public()}


@bp.get("/alerts/nearby")
@require_role("member")
def nearby_alerts():
    user = current_user()
    lat = request.args.get("lat", user.latitude, type=float)
    lng = request.args.get("lng", user.longitude, type=float)
    radius = request.args.get("radius", user.alert_radius_km, type=float)
    if lat is None or lng is None:
        return {"error": "Set your location or allow location access."}, 400

    result = []
    for alert in Alert.query.order_by(Alert.id.desc()).limit(200).all():
        distance = dist(lat, lng, alert.latitude, alert.longitude)
        if distance <= radius:
            result.append({**alert.public(), "distance_km": round(distance, 3)})
    return {"alerts": result}


@bp.get("/sensors/status/nearby")
@require_role("member")
def nearby_sensor_status():
    """Current switch/threshold state, including Normal, for nearby sensors."""
    user = current_user()
    lat = request.args.get("lat", user.latitude, type=float)
    lng = request.args.get("lng", user.longitude, type=float)
    radius = request.args.get("radius", user.alert_radius_km, type=float)
    if lat is None or lng is None:
        return {"error": "Set your location or allow location access."}, 400

    statuses = []
    sensors = Sensor.query.filter_by(active=True).all()
    for sensor in sensors:
        reading = (
            Telemetry.query.filter_by(sensor_id=sensor.sensor_id)
            .order_by(Telemetry.id.desc())
            .first()
        )
        distance = dist(lat, lng, sensor.latitude, sensor.longitude)
        if distance > radius:
            continue

        level = 0 if reading is None else (
            reading.switch_level
            if reading.switch_level is not None
            else level_for(sensor, reading.water_level_m)
        )
        code, label, message = details(level)
        statuses.append(
            {
                "sensor_id": sensor.sensor_id,
                "sensor_name": sensor.name,
                "latitude": sensor.latitude,
                "longitude": sensor.longitude,
                "level": level,
                "code": code,
                "label": label,
                "message": message,
                "switch_level": reading.switch_level if reading else 0,
                "water_level_m": reading.water_level_m if reading else None,
                "source": ("switches" if reading.switch_level is not None else "water_thresholds") if reading else "no_reading",
                "captured_at": reading.captured_at.isoformat() if reading else None,
                "distance_km": round(distance, 3),
            }
        )

    # Any nearby higher-severity sensor takes priority; ties use the nearest one.
    statuses.sort(key=lambda item: (-item["level"], item["distance_km"]))
    current = statuses[0] if statuses else {
        "sensor_id": None,
        "sensor_name": None,
        "level": 0,
        "code": "NORMAL",
        "label": "Normal",
        "message": "No flood switch is active. Conditions are currently normal.",
        "switch_level": 0,
        "water_level_m": None,
        "source": "no_active_reading",
        "captured_at": None,
        "distance_km": None,
    }
    return {"status": current, "statuses": statuses}


@bp.get("/safe-locations/nearest")
@jwt_required()
def nearest_safe():
    user = current_user()
    lat = request.args.get("lat", user.latitude, type=float)
    lng = request.args.get("lng", user.longitude, type=float)
    limit = max(1, min(request.args.get("limit", 5, type=int), 20))
    if lat is None or lng is None:
        return {"error": "Latitude and longitude required."}, 400

    result = []
    for location in SafeLocation.query.filter_by(active=True).all():
        result.append({
            **location.public(),
            "distance_km": round(dist(lat, lng, location.latitude, location.longitude), 3),
        })
    result.sort(key=lambda item: item["distance_km"])
    return {"locations": result[:limit]}
