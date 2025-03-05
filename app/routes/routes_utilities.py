from flask import Blueprint, Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User, BackgroundTask, TestTable
from app.models import db
from app.utils.background_tasks import set_processing
import time
from flask import Flask, jsonify, request, Blueprint, current_app
import threading
import uuid

api_bp = Blueprint("api", __name__, url_prefix="")

load_dotenv()


@api_bp.route('/')
def hello_world():
    return 'Hello, World this is an update!!'



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
    print("Sleeping for 3 seconds")
    time.sleep(3)  # Simulate work
    print("Sleeping for 3 seconds done")
    test_table.result = "Task completed successfully"
    test_table.processing = False
    db.session.commit()
    return True

@api_bp.route('/task/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    try:
        # First get the BackgroundTask to find the username
        background_task = BackgroundTask.query.filter_by(task_id=task_id).first()
        if not background_task:
            return jsonify({
                'status': 'error',
                'message': 'Task not found'
            }), 404

        # Use the username from background_task to get TestTable entry
        user_id = background_task.username
        test_table = TestTable.query.filter_by(username=user_id).first()
        if not test_table:
            return jsonify({
                'status': 'error',
                'message': 'Test table entry not found'
            }), 404
            
        return jsonify({
            'task_id': background_task.task_id,
            'background_task': {
                'processing': background_task.processing,
                'result': background_task.result,
                'created_at': background_task.created_at
            },
            'test_table': {
                'processing': test_table.processing,
                'result': test_table.result,
                'created_at': test_table.created_at
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

