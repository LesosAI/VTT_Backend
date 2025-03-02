from flask import Blueprint, Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User, TestThreading, TestTable
from app.models import db
from ..utils.background_tasks import run_in_background, with_app_context, update_task_status
import time
from flask import Flask, jsonify, request, Blueprint, current_app
import threading
api_bp = Blueprint("api", __name__, url_prefix="")

load_dotenv()


@api_bp.route('/')
def hello_world():
    return 'Hello, World this is an update!!'

def set_processing(f):
    def wrapper(*args, **kwargs):
        try:
            # Get user_id from request arguments
            user_id = request.args.get('user_id')
            
            # Get or create TestThreading instance
            test_thread = TestThreading.query.filter_by(username=user_id).first()
            
            if not test_thread:
                test_thread = TestThreading(username=user_id, processing=False)
                db.session.add(test_thread)
            
            db.session.commit()
            
            # Set processing to True
            test_thread.processing = True
            db.session.commit()
            
            # Extract all needed data from request
            request_data = {
                'user_id': user_id,
                'args': dict(request.args),
                'form': dict(request.form),
                'json': request.get_json(silent=True)
            }
            
            # Start the background process
            app = current_app._get_current_object()
            thread = threading.Thread(
                target=run_task_with_context,
                args=(app, user_id, f, request_data)
            )
            thread.start()
            
            return jsonify({'message': 'Processing started. CSV will be available soon.'}), 202
            
        except Exception as e:
            print(f"Error in processing decorator: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    wrapper.__name__ = f.__name__
    return wrapper

def run_task_with_context(app, username, task_function, request_data):
    with app.app_context():
        test_thread = TestThreading.query.filter_by(username=username).first()
        test_table = TestTable.query.filter_by(username=username).first()
        
        if not test_table:
            test_table = TestTable(username=username, processing=False)
            db.session.add(test_table)
            db.session.commit()

        try:
            # Run the actual task function
            task_function(request_data)
            
            # Update both tables after task completion
            test_thread.processing = False
            test_thread.result = "Task completed successfully"
            db.session.commit()

            print(f"Processing completed for user {username}")

        except Exception as e:
            print(f"Error during processing for user {username}: {e}")
            test_thread.processing = False
            db.session.commit()

@api_bp.route('/threadingtest', methods=['POST'])
@set_processing
def main_function(request_data):
    # This is your long-running task logic
    user_id = request_data['user_id']
    # You can access other request data like this:
    # args_data = request_data['args']
    # form_data = request_data['form']
    # json_data = request_data['json']
    
    test_table = TestTable.query.filter_by(username=user_id).first()
    if not test_table:
        test_table = TestTable(username=user_id, processing=False)
        db.session.add(test_table)
        db.session.commit()

    time.sleep(10)  # Simulate work
    
    test_table.result = "Task completed successfully"
    test_table.processing = False
    db.session.commit()
    return True

@api_bp.route('/threadingtest/status/<username>', methods=['GET'])
def get_task_status(username):
    try:
        test_thread = TestThreading.query.filter_by(username=username).first()
        test_table = TestTable.query.filter_by(username=username).first()
        
        if not test_thread or not test_table:
            return jsonify({
                'status': 'error',
                'message': 'No task found for this user'
            }), 404
            
        return jsonify({
            'processing': test_thread.processing,
            'result': test_thread.result,
            'processing_table': test_table.processing,
            'result_table': test_table.result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

