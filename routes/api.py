"""JSON API used by reception and manager screens."""
import base64
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from flask import Blueprint, current_app, jsonify, request
from models.message import Message
from models.visitor import Visitor
from models.visitor_photo import VisitorPhoto
from models.quick_button import QuickButton
from services.camera import camera_service
from services.csv_export import append_visitor_to_csv
from services.database import db
from services.socketio_service import emit_visitor_registered, update_visitor_status, socketio
from utils.helper import apply_visitor_search, date_range_for_filter, required_fields_present

api_bp = Blueprint("api", __name__)

@api_bp.get("/health")
def health_check(): return jsonify({"status":"ok", "service":"VisionDesk"})

@api_bp.post("/camera/start")
def start_camera():
    try:
        hardware = camera_service.start_camera()
    except Exception as exc:
        current_app.logger.exception("Camera start failed")
        return jsonify({"camera_on": True, "hardware_started": False, "mode": "browser", "error": str(exc)}), 200
    return jsonify({"camera_on": True, "hardware_started": hardware, "mode": "pi" if hardware else "browser"})

@api_bp.post("/camera/stop")
def stop_camera():
    camera_service.stop_camera(); return jsonify({"camera_on":False})

@api_bp.post("/camera/capture")
def capture_photo():
    try:
        return jsonify({"photo_path": camera_service.capture_photo()})
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        current_app.logger.exception("Camera capture failed")
        return jsonify({"error": str(exc)}), 503

@api_bp.post("/camera/upload")
def upload_photo():
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"]); upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"visitor_{datetime.now():%Y%m%d_%H%M%S}_{uuid4().hex[:8]}.jpg"
    output = upload_dir / filename
    if request.files.get("photo"):
        request.files["photo"].save(output)
    else:
        data = (request.get_json(silent=True) or {}).get("image", "")
        if "," in data: data = data.split(",", 1)[1]
        try: output.write_bytes(base64.b64decode(data))
        except Exception: return jsonify({"error":"A valid photo is required."}), 400
    return jsonify({"photo_path":f"/static/uploads/{filename}"})

@api_bp.post("/visitors")
def create_visitor():
    data = request.get_json(silent=True) or request.form.to_dict()
    required = ["name","company","phone","purpose","person_to_meet"]
    valid, error = required_fields_present(data, required)
    if not valid: return jsonify({"error":error}), 400
    paths = data.get("photo_paths") or []
    if isinstance(paths, str): paths = [p for p in paths.split(",") if p]
    primary = paths[0] if paths else (data.get("photo_path") or "").strip()
    visitor = Visitor(name=data["name"].strip(), company=data["company"].strip(), phone=data["phone"].strip(),
        email=(data.get("email") or "").strip(), purpose=data["purpose"].strip(),
        person_to_meet=data["person_to_meet"].strip(), photo_path=primary, status="Waiting")
    db.session.add(visitor); db.session.flush()
    for path in paths: db.session.add(VisitorPhoto(visitor_id=visitor.id, path=path))
    db.session.add(Message(visitor_id=visitor.id, sender="Reception", message="Visitor registration submitted. Waiting for manager approval."))
    db.session.commit(); append_visitor_to_csv(visitor); emit_visitor_registered(visitor)
    return jsonify({"visitor":visitor.to_dict()}), 201

@api_bp.get("/visitors")
def list_visitors():
    start,end = date_range_for_filter(request.args.get("history","today"))
    query = Visitor.query.filter(Visitor.arrival_time.between(start,end))
    if request.args.get("status"): query=query.filter(Visitor.status==request.args["status"])
    query=apply_visitor_search(query,request.args.get("search",""))
    return jsonify({"visitors":[v.to_dict() for v in query.order_by(Visitor.arrival_time.desc()).all()]})

@api_bp.get("/visitors/<int:visitor_id>")
def get_visitor(visitor_id):
    visitor = Visitor.query.get_or_404(visitor_id)
    return jsonify({"visitor": visitor.to_dict()})

@api_bp.patch("/visitors/<int:visitor_id>/status")
def change_status(visitor_id):
    data=request.get_json(silent=True) or {}
    try: visitor=update_visitor_status(visitor_id,data.get("status",""),data.get("message"))
    except ValueError as exc: return jsonify({"error":str(exc)}),400
    return jsonify({"visitor":visitor.to_dict()})

@api_bp.post("/messages")
def create_message():
    data=request.get_json(silent=True) or {}; text=(data.get("message") or "").strip()
    if not text: return jsonify({"error":"Message is required."}),400
    record=Message(visitor_id=data.get("visitor_id") or None,sender="Manager",message=text)
    db.session.add(record); db.session.commit(); payload={"message":record.to_dict()}
    socketio.emit("reception_message",payload,to="reception"); socketio.emit("message_sent",payload,to="manager")
    return jsonify(payload),201

@api_bp.get("/messages")
def list_messages(): return jsonify({"messages":[m.to_dict() for m in Message.query.order_by(Message.timestamp.desc()).limit(50).all()]})

@api_bp.get("/quick-buttons")
def quick_buttons():
    try:
        q = QuickButton.query.filter(QuickButton.hidden==False).order_by(QuickButton.sort_order,QuickButton.id).all()
    except Exception:
        # Older installations may not have the `hidden` column; return all buttons
        q = QuickButton.query.order_by(QuickButton.sort_order,QuickButton.id).all()
    return jsonify({"buttons":[b.to_dict() for b in q]})

@api_bp.post("/quick-buttons")
def add_quick_button():
    data=request.get_json(silent=True) or {}; label=(data.get("label") or "").strip(); message=(data.get("message") or "").strip()
    if not label or not message: return jsonify({"error":"Button name and message are required."}),400
    button=QuickButton(label=label,message=message,is_custom=True,sort_order=QuickButton.query.count())
    db.session.add(button); db.session.commit(); socketio.emit("quick_buttons_updated",{},to="manager")
    return jsonify({"button":button.to_dict()}),201

@api_bp.delete("/quick-buttons/<int:button_id>")
def delete_quick_button(button_id):
    button=QuickButton.query.get_or_404(button_id)
    data = request.get_json(silent=True) or {}
    force = bool(data.get("force", False) or request.args.get("force") == "true")
    if not button.is_custom:
        if not force:
            return jsonify({"error":"This is a built-in button. Pass '{\"force\":true}' in request body to confirm deletion."}), 400
        # Prefer to mark hidden; if column doesn't exist, fallback to delete
        try:
            button.hidden = True
            db.session.add(button)
        except Exception:
            db.session.delete(button)
    else:
        db.session.delete(button)
    db.session.commit()
    socketio.emit("quick_buttons_updated",{},to="manager")
    return jsonify({"deleted":True})