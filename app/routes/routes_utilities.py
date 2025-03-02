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
            
            # Call the original function
            return f(*args, **kwargs)
            
        except Exception as e:
            print(f"Error in processing decorator: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    # Preserve the original function's metadata
    wrapper.__name__ = f.__name__
    return wrapper

@api_bp.route('/threadingtest', methods=['POST'])
@set_processing
def Image_to_CSV():
    try:
        start_time = time.time()
        user_id = request.args.get('user_id')
        
        # You can remove the manual processing=True setting since the decorator handles it
        test_table = TestTable.query.filter_by(username=user_id).first()
        
        if not test_table:
            test_table = TestTable(username=user_id, processing=False)
            db.session.add(test_table)
        
        db.session.commit()
        
        # Start the background process
        app = current_app._get_current_object()
        function_to_run_and_monitor(app, user_id, request, long_running_task)

        return jsonify({'message': 'Processing started. CSV will be available soon.'}), 202

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)}), 500

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

def function_to_run_and_monitor(app, username, request, long_running_task):
    print("Starting start_transcription_and_monitor function...")
    thread = threading.Thread(target=long_running_task,
                              args=(app, username, request))
    thread.start()


    print("Thread started.")

def long_running_task(app, username, request):
    with app.app_context():
        test_thread = TestThreading.query.filter_by(username=username).first()
        test_table = TestTable.query.filter_by(username=username).first()
        
        if not test_thread or not test_table:
            print(f"Required entries for user {username} not found.")
            return

        try:
            # Simulate work
            time.sleep(10)
            
            # Update both tables
            test_thread.processing = False
            test_thread.result = "Task completed successfully"
            test_table.result = "Task completed successfully"
            test_table.processing = False
            db.session.commit()

            print(f"Processing completed for user {username}")

        except Exception as e:
            print(f"Error during processing for user {username}: {e}")
            test_thread.processing = False
            test_table.processing = False
            db.session.commit()