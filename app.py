"""VisionDesk application entry point."""
import os
import socket
from flask import Flask
from config import Config
from routes.api import api_bp
from routes.manager import manager_bp
from routes.reception import reception_bp
from services.database import db, init_database
from services.led import led_service
from services.socketio_service import register_socketio_events, socketio


def get_lan_ip():
    """Return the address another device on the local network can use."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        address = probe.getsockname()[0]
    except OSError:
        try:
            address = socket.gethostbyname(socket.gethostname())
        except OSError:
            address = "127.0.0.1"
    finally:
        probe.close()
    return address


def print_access_urls():
    lan_ip = get_lan_ip()
    print("\n" + "=" * 66, flush=True)
    print(" VISIONDESK IS READY", flush=True)
    print("=" * 66, flush=True)
    print(f" RECEPTION URL: http://localhost:{Config.PORT}/reception", flush=True)
    print(f" MANAGER URL:   http://localhost:{Config.PORT}/manager", flush=True)
    print("-" * 66, flush=True)
    print(f" MANAGER ON SECOND PI: http://{lan_ip}:{Config.PORT}/manager", flush=True)
    print("=" * 66 + "\n", flush=True)


def find_available_port(start_port, max_tries=20):
    """Return the first available TCP port starting from start_port."""
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
            try:
                test_socket.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available port found between {start_port} and {start_port + max_tries - 1}")


def resolve_runtime_port():
    """Use the configured port when it is free, otherwise fall back to an open port."""
    try:
        return find_available_port(Config.PORT)
    except RuntimeError:
        return Config.PORT


def create_app():
    application = Flask(__name__, instance_relative_config=True)
    application.config.from_object(Config)
    db.init_app(application)
    socketio.init_app(application, cors_allowed_origins=application.config["SOCKETIO_CORS_ALLOWED_ORIGINS"], async_mode=application.config["SOCKETIO_ASYNC_MODE"])
    application.register_blueprint(reception_bp)
    application.register_blueprint(manager_bp)
    application.register_blueprint(api_bp, url_prefix="/api")
    register_socketio_events(socketio)
    with application.app_context():
        init_database()
        led_service.set_ready()
    return application


app = create_app()
if os.environ.get("VISIONDESK_SHOW_URLS", "true").lower() == "true":
    print_access_urls()

if __name__ == "__main__":
    runtime_port = resolve_runtime_port()
    if runtime_port != Config.PORT:
        print(f"Port {Config.PORT} is busy; using {runtime_port} instead.", flush=True)
    socketio.run(app, host=Config.HOST, port=runtime_port, debug=Config.DEBUG, allow_unsafe_werkzeug=True)