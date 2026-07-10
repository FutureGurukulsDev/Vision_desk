"""Manager page routes."""
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session

manager_bp = Blueprint("manager", __name__)


def manager_login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("manager_logged_in"):
            next_page = request.path
            return redirect(url_for("manager.manager_login_page", next=next_page))
        return view_func(*args, **kwargs)
    return wrapped_view


@manager_bp.route("/manager/login", methods=["GET", "POST"])
def manager_login_page():
    error = None
    identifier = ""
    next_url = request.args.get("next") or request.form.get("next") or url_for("manager.manager_page")

    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        password = (request.form.get("password") or "").strip()
        if not identifier or not password:
            error = "Enter user name or email and password."
        else:
            session.permanent = True
            session["manager_logged_in"] = True
            session["manager_username"] = identifier
            return redirect(next_url)

    return render_template(
        "login.html",
        page_title="Manager Login",
        error=error,
        mode="login",
        identifier=identifier,
        allow_signup=False,
        role="manager",
        next=next_url,
    )


@manager_bp.route("/manager/logout")
def manager_logout_page():
    session.pop("manager_logged_in", None)
    session.pop("manager_username", None)
    return redirect(url_for("manager.manager_login_page"))


@manager_bp.route("/manager")
@manager_login_required
def manager_page():
    return render_template(
        "manager_home.html",
        page_title="Manager Desk",
        manager_username=session.get("manager_username"),
    )


@manager_bp.route("/manager/visitors")
@manager_login_required
def manager_visitors_page():
    return render_template(
        "manager.html",
        page_title="Visitor Dashboard",
        manager_username=session.get("manager_username"),
    )


@manager_bp.route("/manager/quick-buttons")
@manager_login_required
def manager_quick_buttons_page():
    return render_template(
        "quick_buttons.html",
        page_title="Quick Buttons",
        manager_username=session.get("manager_username"),
    )
