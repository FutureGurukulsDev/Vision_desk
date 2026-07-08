"""Camera capture service using Picamera2 with OpenCV fallback support."""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import current_app


class CameraService:
    """Handles Raspberry Pi camera capture and development fallbacks."""

    def __init__(self) -> None:
        self._camera = None
        self._initialized = False

    def _initialize_picamera(self) -> bool:
        """Initialize Picamera2 when available on Raspberry Pi OS."""
        if self._initialized:
            return self._camera is not None

        self._initialized = True
        if not current_app.config.get("CAMERA_ENABLED", True):
            return False

        try:
            from picamera2 import Picamera2
        except ImportError:
            current_app.logger.warning("Picamera2 not installed; using browser upload fallback.")
            self._initialized = False
            return False

        try:
            self._camera = Picamera2()
            config = self._camera.create_still_configuration(
                main={
                    "size": (
                        current_app.config["CAMERA_WIDTH"],
                        current_app.config["CAMERA_HEIGHT"],
                    )
                }
            )
            self._camera.configure(config)
            self._camera.start()
            return True
        except Exception as exc:
            current_app.logger.warning("Pi camera initialization failed: %s", exc)
            self._camera = None
            self._initialized = False
            return False

    def start_camera(self) -> bool:
        """Start the camera so the reception screen can prepare for capture."""
        return self._initialize_picamera()

    def stop_camera(self) -> None:
        """Stop the active camera session when the operator turns it off."""
        if self._camera:
            try:
                self._camera.stop()
            except RuntimeError:
                current_app.logger.info("Camera was already stopped.")
            self._camera = None
            self._initialized = False

    def capture_photo(self) -> str:
        """Capture a visitor photo and return its relative static path."""
        upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
        upload_dir.mkdir(parents=True, exist_ok=True)
        filename = f"visitor_{datetime.now():%Y%m%d_%H%M%S}_{uuid4().hex[:8]}.jpg"
        output_path = upload_dir / filename

        if self._initialize_picamera() and self._camera:
            try:
                self._camera.capture_file(str(output_path))
            except Exception as exc:
                current_app.logger.warning("Pi camera capture failed, using placeholder: %s", exc)
                self._write_placeholder_image(output_path)
        else:
            self._write_placeholder_image(output_path)

        return f"/static/uploads/{filename}"

    @staticmethod
    def _write_placeholder_image(output_path: Path) -> None:
        """Create a local placeholder image when Pi camera hardware is absent."""
        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("Install Picamera2 or OpenCV to capture photos.") from exc

        image = np.full((720, 1280, 3), (245, 247, 250), dtype=np.uint8)
        cv2.putText(
            image,
            "VisionDesk Camera Preview",
            (260, 340),
            cv2.FONT_HERSHEY_SIMPLEX,
            2,
            (42, 70, 108),
            4,
            cv2.LINE_AA,
        )
        cv2.putText(
            image,
            "Development fallback image",
            (390, 420),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (85, 99, 117),
            2,
            cv2.LINE_AA,
        )
        cv2.imwrite(str(output_path), image)


camera_service = CameraService()

