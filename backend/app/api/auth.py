from flask import Blueprint,request
from flask_jwt_extended import create_access_token,jwt_required,get_jwt_identity
from ..models import User
from ..extensions import db
bp=Blueprint("auth",__name__)
@bp.post("/login")
def login():
    data=request.get_json() or {}; mobile=str(data.get("mobile","")).strip(); password=str(data.get("password","")); requested=str(data.get("role","member"))
    user=User.query.filter_by(mobile=mobile).first()
    if not user or not user.active or user.role!=requested or not user.check_password(password): return {"error":"Invalid mobile, password, or role."},401
    token=create_access_token(identity=str(user.id),additional_claims={"role":user.role,"mobile":user.mobile})
    return {"access_token":token,"user":user.public()}
@bp.post("/register")
def register():
    data=request.get_json() or {}; mobile=str(data.get("mobile","")).strip(); name=str(data.get("name","")).strip(); password=str(data.get("password",""))
    if not mobile or not name or len(password)<8: return {"error":"mobile, name and an 8+ character password are required."},400
    if User.query.filter_by(mobile=mobile).first(): return {"error":"Mobile already registered."},409
    u=User(mobile=mobile,name=name,role="member",latitude=data.get("latitude"),longitude=data.get("longitude"),alert_radius_km=float(data.get("alert_radius_km",10)))
    u.set_password(password); db.session.add(u); db.session.commit(); return {"user":u.public()},201
@bp.get("/me")
@jwt_required()
def me(): return {"user":User.query.get(int(get_jwt_identity())).public()}
