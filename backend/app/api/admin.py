from flask import Blueprint,request
from ..utils.auth import require_role,current_user
from ..models import Sensor,SafeLocation,User,Alert,Telemetry
from ..services.alert_engine import level_for, details
from ..extensions import db
from ..services.notification_service import notify_user,sms_if_configured
bp=Blueprint("admin",__name__)
@bp.get("/sensors")
@require_role("admin")
def sensors():
    result = []
    for sensor in Sensor.query.filter_by(active=True).order_by(Sensor.id.desc()).all():
        item = sensor.public()
        reading = Telemetry.query.filter_by(sensor_id=sensor.sensor_id).order_by(Telemetry.id.desc()).first()
        level = 0 if reading is None else (reading.switch_level if reading.switch_level is not None else level_for(sensor, reading.water_level_m))
        code, label, message = details(level)
        item.update({
            "level": level, "code": code, "label": label, "message": message,
            "water_level_m": reading.water_level_m if reading else None,
            "switch_level": reading.switch_level if reading else 0,
            "latest_reading": reading.public() if reading else None,
        })
        result.append(item)
    return {"sensors": result}

@bp.delete("/sensors/<int:sensor_pk>")
@require_role("admin")
def delete_sensor(sensor_pk):
    sensor = Sensor.query.filter_by(id=sensor_pk, active=True).first_or_404()
    # Soft-delete: preserve historical telemetry and alert records for audit/event history.
    sensor.active = False
    db.session.commit()
    return {"message": "Sensor deleted from the active network.", "sensor_id": sensor.sensor_id}
@bp.post("/sensors")
@require_role("admin")
def add_sensor():
    d=request.get_json() or {}; required=["sensor_id","name","latitude","longitude","level1_m","level2_m","level3_m","level4_m"]
    if any(k not in d for k in required): return {"error":"All sensor identity, location and four thresholds are required."},400
    if Sensor.query.filter_by(sensor_id=d["sensor_id"]).first(): return {"error":"sensor_id already exists"},409
    key=Sensor.new_key(); s=Sensor(sensor_id=d["sensor_id"],name=d["name"],latitude=float(d["latitude"]),longitude=float(d["longitude"]),level1_m=float(d["level1_m"]),level2_m=float(d["level2_m"]),level3_m=float(d["level3_m"]),level4_m=float(d["level4_m"]),device_key_hash=Sensor.hash_key(key))
    if not (s.level1_m<s.level2_m<s.level3_m<s.level4_m): return {"error":"Thresholds must increase from Level 1 to Level 4."},400
    db.session.add(s); db.session.commit(); return {"sensor":s.public(),"device_key":key},201
@bp.get("/safe-locations")
@require_role("admin")
def safe_locations(): return {"locations":[x.public() for x in SafeLocation.query.order_by(SafeLocation.id.desc()).all()]}
@bp.post("/safe-locations")
@require_role("admin")
def add_safe_location():
    d=request.get_json() or {}
    if not all(k in d for k in ["name","address","latitude","longitude"]): return {"error":"name, address, latitude, longitude required"},400
    x=SafeLocation(name=d["name"],address=d["address"],latitude=float(d["latitude"]),longitude=float(d["longitude"]),capacity=d.get("capacity")); db.session.add(x); db.session.commit(); return {"location":x.public()},201
@bp.post("/warnings/direct")
@require_role("admin")
def direct_warning():
    d=request.get_json() or {}; mobile=str(d.get("mobile","")).strip(); title=str(d.get("title","Emergency warning")); message=str(d.get("message","")).strip(); severity=str(d.get("severity","WARNING"))
    u=User.query.filter_by(mobile=mobile,active=True).first()
    if not u: return {"error":"Active member with that mobile number was not found."},404
    if not message: return {"error":"message is required"},400
    n=notify_user(u,title,message,severity,"admin_direct")
    sms=sms_if_configured(u.mobile,f"{title}: {message}")
    return {"notification":n.public(),"sms":sms}
@bp.get("/alerts")
@require_role("admin")
def alerts(): return {"alerts":[a.public() for a in Alert.query.order_by(Alert.id.desc()).limit(100).all()]}
