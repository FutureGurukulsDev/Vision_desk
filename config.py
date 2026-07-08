"""Application configuration for VisionDesk."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Central Flask and hardware configuration."""

    SECRET_KEY = os.environ.get("VISIONDESK_SECRET_KEY", "change-this-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "VISIONDESK_DATABASE_URI",
        f"sqlite:///{BASE_DIR / 'database.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024

    VISITOR_CSV_PATH = Path(
        os.environ.get("VISIONDESK_VISITOR_CSV_PATH", BASE_DIR / "exports" / "visitors.csv")
    )

    HOST = os.environ.get("VISIONDESK_HOST", "0.0.0.0")
    PORT = int(os.environ.get("VISIONDESK_PORT", "5000"))
    DEBUG = os.environ.get("VISIONDESK_DEBUG", "false").lower() == "true"

    CAMERA_ENABLED = os.environ.get("VISIONDESK_CAMERA_ENABLED", "true").lower() == "true"
    CAMERA_WIDTH = int(os.environ.get("VISIONDESK_CAMERA_WIDTH", "1280"))
    CAMERA_HEIGHT = int(os.environ.get("VISIONDESK_CAMERA_HEIGHT", "720"))

    LED_ENABLED = os.environ.get("VISIONDESK_LED_ENABLED", "true").lower() == "true"
    LED_RED_PIN = int(os.environ.get("VISIONDESK_LED_RED_PIN", "17"))
    LED_GREEN_PIN = int(os.environ.get("VISIONDESK_LED_GREEN_PIN", "27"))
    LED_BLUE_PIN = int(os.environ.get("VISIONDESK_LED_BLUE_PIN", "22"))

    SOCKETIO_ASYNC_MODE = os.environ.get("VISIONDESK_SOCKETIO_ASYNC_MODE", "threading")
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.environ.get(
        "VISIONDESK_SOCKETIO_CORS_ALLOWED_ORIGINS",
        "*",
    )
