from functools import wraps
import threading
from flask import current_app
from typing import Callable, Any
from ..models import db

def run_in_background(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    A decorator that runs the decorated function in a background thread.
    The decorated function must be used within a Flask application context.
    
    Usage:
    @run_in_background
    def my_long_running_task(app, *args, **kwargs):
        with app.app_context():
            # Your long running code here
            pass
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        app = current_app._get_current_object()
        thread = threading.Thread(target=f, args=(app,) + args, kwargs=kwargs)
        thread.daemon = True  # Daemonize thread to allow app to exit
        thread.start()
        return thread
    return wrapper

def update_task_status(user_id: str, status: bool) -> None:
    """
    Update the processing status for a user in the database.
    
    Args:
        user_id: The ID or username of the user
        status: The processing status to set (True/False)
    """
    from ..models.user import User  # Import here to avoid circular imports
    
    try:
        user = User.query.filter_by(username=user_id).first()
        if user:
            user.processing = status
            db.session.commit()
    except Exception as e:
        print(f"Error updating task status: {e}")
        db.session.rollback()

def with_app_context(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    A decorator that ensures the function runs within the Flask application context.
    
    Usage:
    @with_app_context
    def my_db_function(*args, **kwargs):
        # Your database operations here
        pass
    """
    @wraps(f)
    def wrapper(app, *args, **kwargs):
        with app.app_context():
            return f(*args, **kwargs)
    return wrapper 