"""Reception page routes."""

from flask import Blueprint, render_template

reception_bp = Blueprint("reception", __name__)


@reception_bp.route("/")
@reception_bp.route("/reception")
def reception_page():
    """Render the visitor registration and waiting screen."""
    return render_template("reception.html", page_title="Reception")
