"""Database initialization."""
from pathlib import Path
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

db = SQLAlchemy()

BUILT_IN_QUICK_BUTTONS = [
    ("Approve", "Approve the current visitor."),
    ("Reject", "Reject the current visitor."),
    ("Busy", "Mark the manager as busy."),
    ("Meeting Started", "The meeting has started."),
    ("Meeting Finished", "The meeting has finished."),
    ("Send Water", "Please serve water to the visitor."),
    ("Send Coffee", "Please serve coffee to the visitor."),
    ("Send Tea", "Please serve tea to the visitor."),
    ("Offer Refreshments", "Please offer refreshments to the visitor."),
    ("Call Reception", "Please call reception immediately."),
    ("Call Person", "Please inform the person being visited that their visitor has arrived."),
    ("Request ID Proof", "Please request and verify the visitor ID proof."),
    ("Collect Documents", "Please collect the required documents from the visitor."),
    ("Send Visitor In", "Please send the visitor in for the meeting."),
    ("Escort Visitor", "Please arrange an escort for the visitor."),
    ("Prepare Room", "Please prepare the meeting room for the visitor."),
    ("Meeting Delayed", "Please inform the visitor that the meeting is delayed."),
    ("Manager Unavailable", "Please inform the visitor that the manager is currently unavailable."),
    ("Custom Message", "Open custom message composer."),
]

def ensure_table_columns(model_class):
    inspector = inspect(db.engine)
    table_name = model_class.__tablename__
    if not inspector.has_table(table_name):
        return

    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    for column in model_class.__table__.columns:
        if column.name in existing_columns:
            continue

        column_type = column.type.compile(dialect=db.engine.dialect)
        default_sql = ""
        if column.default is not None and hasattr(column.default, "arg"):
            default_value = column.default.arg
            if isinstance(default_value, bool):
                default_sql = f" DEFAULT {'1' if default_value else '0'}"
            elif isinstance(default_value, str):
                default_sql = f" DEFAULT '{default_value}'"
            else:
                default_sql = f" DEFAULT {default_value}"

        db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column.name} {column_type}{default_sql}"))

    db.session.commit()


def init_database():
    Path(current_app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(current_app.config["VISITOR_CSV_PATH"]).parent.mkdir(parents=True, exist_ok=True)
    from models.visitor import Visitor
    from models.message import Message
    from models.visitor_photo import VisitorPhoto
    from models.quick_button import QuickButton
    db.create_all()
    ensure_table_columns(QuickButton)
    existing = {button.label for button in QuickButton.query.filter_by(is_custom=False).all()}
    for order, (label, message) in enumerate(BUILT_IN_QUICK_BUTTONS):
        if label not in existing:
            db.session.add(QuickButton(label=label, message=message, is_custom=False, sort_order=order))
    db.session.commit()