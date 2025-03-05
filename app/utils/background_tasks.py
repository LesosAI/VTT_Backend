from flask import request, jsonify, current_app
import threading
import uuid
from app.models import db
from app.models.user import BackgroundTask, TestTable


def set_processing(f):
    def wrapper(*args, **kwargs):
        try:
            user_id = request.args.get('user_id')
            task_id = str(uuid.uuid4())  # Generate unique task ID
            
            # Create new BackgroundTask instance for this specific task
            background_task = BackgroundTask(
                username=user_id,
                task_id=task_id,
                processing=True
            )
            db.session.add(background_task)
            db.session.commit()
            
            # Extract all needed data from request
            request_data = {
                'user_id': user_id,
                'task_id': task_id,  # Pass task_id to the background process
                'args': dict(request.args),
                'form': dict(request.form),
                'json': request.get_json(silent=True)
            }
            
            # Start the background process
            app = current_app._get_current_object()
            thread = threading.Thread(
                target=run_task_with_context,
                args=(app, user_id, task_id, f, request_data)
            )
            thread.start()
            
            return jsonify({
                'message': 'Processing started',
                'task_id': task_id  # Return task_id to client for status checking
            }), 202
            
        except Exception as e:
            print(f"Error in processing decorator: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    wrapper.__name__ = f.__name__
    return wrapper

def run_task_with_context(app, username, task_id, task_function, request_data):
    with app.app_context():
        background_task = BackgroundTask.query.filter_by(task_id=task_id).first()
        test_table = TestTable.query.filter_by(username=username).first()
        
        if not test_table:
            test_table = TestTable(username=username, processing=False)
            db.session.add(test_table)
            db.session.commit()

        try:
            # Run the actual task function
            task_function(request_data)
            
            # Update both tables after task completion
            background_task.processing = False
            background_task.result = "Task completed successfully"
            db.session.commit()

            print(f"Processing completed for user {username}")

        except Exception as e:
            print(f"Error during processing for user {username}: {e}")
            background_task.processing = False
            db.session.commit()