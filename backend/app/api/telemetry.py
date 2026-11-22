from datetime import datetime, timezone
from math import isfinite
from flask import Blueprint, request
from ..models import Sensor, Telemetry, Alert
from ..extensions import db
from ..services.alert_engine import level_for, details
from ..services.notification_service import notify_nearby_users, emit_nearby_sensor_status
from ..services.central_forwarder import forward_event
from .. import socketio

bp = Blueprint("telemetry", __name__)


@bp.post("/telemetry")
def ingest():
    key = request.headers.get("X-Device-Key", "")
    data = request.get_json() or {}
    sensor_id = str(data.get("sensor_id", "")).strip()
    sensor = Sensor.query.filter_by(sensor_id=sensor_id, active=True).first()
    if not sensor or not key or not sensor.check_key(key):
        return {"error": "Unknown sensor or invalid device key."}, 401

    try:
        water = float(data["water_level_m"])
        pressure = None if data.get("pressure_kpa") is None else float(data["pressure_kpa"])
        battery = None if data.get("battery_v") is None else float(data["battery_v"])
    except (KeyError, ValueError, TypeError):
        return {"error": "water_level_m is required and numeric; optional numeric fields must be valid."}, 400

    switch_level = data.get("switch_level")
    if switch_level is not None:
        # JSON bools are integers in Python, but are not valid switch-level values.
        if isinstance(switch_level, bool) or not isinstance(switch_level, (int, float)):
            return {"error": "switch_level must be an integer from 0 to 4."}, 400
        if not isfinite(float(switch_level)) or int(switch_level) != switch_level or not 0 <= int(switch_level) <= 4:
            return {"error": "switch_level must be an integer from 0 to 4."}, 400
        switch_level = int(switch_level)

    captured = data.get("captured_at")
    try:
        captured_at = datetime.fromisoformat(captured.replace("Z", "+00:00")) if captured else datetime.now(timezone.utc)
    except Exception:
        return {"error": "captured_at must be ISO-8601."}, 400

    previous = Telemetry.query.filter_by(sensor_id=sensor_id).order_by(Telemetry.id.desc()).first()
    previous_level = 0
    if previous:
        previous_level = (
            previous.switch_level
            if previous.switch_level is not None
            else level_for(sensor, previous.water_level_m)
        )

    reading = Telemetry(
        sensor_id=sensor_id,
        water_level_m=water,
        pressure_kpa=pressure,
        battery_v=battery,
        switch_level=switch_level,
        latitude=data.get("latitude", sensor.latitude),
        longitude=data.get("longitude", sensor.longitude),
        captured_at=captured_at,
    )

    sensor.last_seen_at = datetime.now(timezone.utc)
    db.session.add(reading)
    db.session.flush()

    # When the new firmware sends switch_level, that physical switch state is
    # authoritative. Older firmware without the field keeps using thresholds.
    level = switch_level if switch_level is not None else level_for(sensor, water)
    print("\n========== FLOODGUARD ALERT DEBUG ==========")
    print("Sensor ID:", sensor_id)
    print("Previous telemetry level:", previous_level)
    print("Current telemetry level:", level)
    print("Previous water level:", previous.water_level_m if previous else None)
    print("Previous switch level:", previous.switch_level if previous else None)
    print("Current water level:", water)
    print("Current switch level:", switch_level)
    print("Should create alert:", level != previous_level and level > 0)
    print("============================================\n")
    code, title, message = details(level)
    status = {
        "sensor_id": sensor_id,
        "sensor_name": sensor.name,
        "level": level,
        "code": code,
        "label": title,
        "message": message,
        "switch_level": switch_level,
        "water_level_m": water,
        "source": "switches" if switch_level is not None else "water_thresholds",
        "latitude": reading.latitude if reading.latitude is not None else sensor.latitude,
        "longitude": reading.longitude if reading.longitude is not None else sensor.longitude,
        "captured_at": reading.captured_at.isoformat(),
    }

    alert = None
    # Create an alert only when severity rises. This avoids a new red alert
    # record/notification every few seconds while a switch remains active.
    if level != previous_level and level > 0:
        alert = Alert(
            sensor_id=sensor_id,
            level=level,
            code=code,
            title=title,
            message=message,
            water_level_m=water,
            latitude=status["latitude"],
            longitude=status["longitude"],
        )
        db.session.add(alert)
        db.session.flush()

    db.session.commit()

    socketio.emit(
        "telemetry:update",
        {
            "sensor": sensor.public(),
            "reading": reading.public(),
            "alert": alert.public() if alert else None,
            "status": status,
        },
        room="admins",
    )

    member_status = emit_nearby_sensor_status(status)

    forward = {
        "event": "telemetry",
        "reading": reading.public(),
        "status": status,
        "alert": alert.public() if alert else None,
    }
    central = forward_event(forward)
    nearby_notified = notify_nearby_users(alert) if alert else 0

    return {
        "reading": reading.public(),
        "status": status,
        "alert": alert.public() if alert else None,
        "nearby_users_notified": nearby_notified,
        "nearby_users_updated": member_status,
        "central_forward": central,
    }, 201
