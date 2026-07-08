"""Database model package for VisionDesk."""
from models.message import Message
from models.visitor import Visitor
from models.visitor_photo import VisitorPhoto
from models.quick_button import QuickButton
__all__ = ["Message", "Visitor", "VisitorPhoto", "QuickButton"]