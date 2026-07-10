"""Reception page routes."""

from flask import Blueprint, render_template, request, redirect, url_for

reception_bp = Blueprint("reception", __name__)


@reception_bp.route("/")
@reception_bp.route("/reception")
def reception_page():
    """Render the visitor registration and waiting screen."""
    return render_template("reception.html", page_title="Reception", active_panel="registration")


@reception_bp.route("/reception/queue")
def reception_queue_page():
    """Render the visitor queue page."""
    return render_template("reception.html", page_title="Visitor Queue", active_panel="queue")


@reception_bp.route("/login", methods=["GET", "POST"])
def login_page():
    """Render a login screen that accepts either username or email and supports signup."""
    error = None
    mode = "login"
    identifier = ""
    username = ""
    email = ""

    if request.method == "POST":
        mode = request.form.get("mode", "login")
        password = (request.form.get("password") or "").strip()

        if mode == "signup":
            username = (request.form.get("username") or "").strip()
            email = (request.form.get("email") or "").strip()
            if not username or not email or not password:
                error = "Enter a user name, email, and password to create an account."
            else:
                return redirect(url_for("reception.reception_page"))
        else:
            identifier = (request.form.get("identifier") or "").strip()
            if not identifier or not password:
                error = "Enter both user name/email and password."
            else:
                return redirect(url_for("reception.reception_page"))

    return render_template(
        "login.html",
        page_title="Login",
        error=error,
        mode=mode,
        identifier=identifier,
        username=username,
        email=email,
        allow_signup=True,
        role="reception",
        next=url_for("reception.reception_page"),
    )


@reception_bp.route("/reception/visitor/<int:visitor_id>")
def reception_visitor_page(visitor_id):
    """Render the reception visitor details and manager instruction screen."""
    return render_template("reception_details.html", page_title="Visitor Details", visitor_id=visitor_id)
