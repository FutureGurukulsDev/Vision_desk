"""Manager page routes."""
from flask import Blueprint, render_template
manager_bp=Blueprint("manager",__name__)
@manager_bp.route("/manager")
def manager_page(): return render_template("manager_home.html",page_title="Manager Desk")
@manager_bp.route("/manager/visitors")
def manager_visitors_page(): return render_template("manager.html",page_title="Visitor Dashboard")
@manager_bp.route("/manager/quick-buttons")
def manager_quick_buttons_page(): return render_template("quick_buttons.html",page_title="Quick Buttons")