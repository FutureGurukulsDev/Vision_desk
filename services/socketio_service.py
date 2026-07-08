"""SocketIO service and realtime event handlers."""

from flask import request
from flask_socketio import SocketIO, emit, join_room

from models.message import Message
from models.visitor import Visitor
from services.database import db
from services.led import led_service

socketio = SocketIO()

VALID_STATUSES = {
    "Waiting",
    "Approved",
    "Rejected",
    "Busy",
    "Meeting Started",
    "Meeting Finished",
}


def register_socketio_events(socketio_instance: SocketIO) -> None:
    """Register SocketIO event handlers for manager and reception screens."""

    @socketio_instance.on("connect")
    def handle_connect() -> None:
        emit("connection_ack", {"message": "Connected to VisionDesk."})

    @socketio_instance.on("join_role")
    def handle_join_role(data: dict) -> None:
        role = data.get("role", "reception")
        if role in {"manager", "reception"}:
            join_room(role)
            emit("role_joined", {"role": role})

    @socketio_instance.on("join_visitor")
    def handle_join_visitor(data: dict) -> None:
        visitor_id = data.get("visitor_id")
        if visitor_id:
            join_room(f"visitor:{visitor_id}")
            emit("visitor_joined", {"visitor_id": visitor_id})

    @socketio_instance.on("manager_status")
    def handle_manager_status(data: dict) -> None:
        visitor_id = data.get("visitor_id")
        status = data.get("status")
        message = data.get("message", status)
        update_visitor_status(visitor_id, status, message)

    @socketio_instance.on("manager_message")
    def handle_manager_message(data: dict) -> None:
        visitor_id = data.get("visitor_id")
        message = data.get("message", "").strip()
        if not message:
            emit("operation_error", {"message": "Message cannot be empty."}, to=request.sid)
            return

        visitor = Visitor.query.get(visitor_id) if visitor_id else None
        record = Message(visitor_id=visitor.id if visitor else None, sender="Manager", message=message)
        db.session.add(record)
        db.session.commit()

        payload = {
            "visitor": visitor.to_dict() if visitor else None,
            "message": record.to_dict(),
        }
        socketio_instance.emit("message_sent", payload, to="manager")
        socketio_instance.emit("reception_message", payload, to="reception")
        if visitor:
            socketio_instance.emit("visitor_message", payload, to=f"visitor:{visitor.id}")


def emit_visitor_registered(visitor: Visitor) -> None:
    """Broadcast a newly registered visitor to all screens."""
    led_service.set_waiting()
    payload = {"visitor": visitor.to_dict()}
    socketio.emit("visitor_registered", payload, to="manager")
    socketio.emit("reception_waiting", payload, to="reception")


def update_visitor_status(visitor_id: int, status: str, message: str | None = None) -> Visitor:
    """Update visitor status and broadcast it through SocketIO."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Unsupported status: {status}")

    visitor = Visitor.query.get_or_404(visitor_id)
    visitor.status = status
    record = Message(
        visitor_id=visitor.id,
        sender="Manager",
        message=message or status,
    )
    db.session.add(record)
    db.session.commit()

    if status == "Approved":
        led_service.set_approved()
    elif status == "Rejected":
        led_service.set_rejected()
    elif status in {"Waiting", "Busy"}:
        led_service.set_waiting()

    payload = {"visitor": visitor.to_dict(), "message": record.to_dict()}
    socketio.emit("visitor_status_updated", payload, to="manager")
    socketio.emit("visitor_status_updated", payload, to="reception")
    socketio.emit("visitor_status_updated", payload, to=f"visitor:{visitor.id}")
    return visitor
