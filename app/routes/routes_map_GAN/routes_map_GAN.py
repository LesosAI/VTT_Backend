import threading
import uuid
from flask import Blueprint, request, jsonify, send_file, make_response
from app.utils.tasks import background_generate_map, tasks
from app.models.user import CharacterArt, User, db, Tag, Map
import requests
from datetime import datetime
from PIL import Image, ImageDraw
import io
from app.utils.davinco_microservice.use_lora.use_image_lora import generate_map_art
import os
from dotenv import load_dotenv
api_map_GAN = Blueprint("api_map_GAN", __name__, url_prefix="/api")

load_dotenv()
@api_map_GAN.route('/generate-map', methods=['POST'])
def generate_map():
    data = request.json

    if not data.get('username'):
        return jsonify({'error': 'Username is required'}), 400

    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending'}
    thread = threading.Thread(target=background_generate_map, args=(task_id, data))
    thread.start()

    return jsonify({'task_id': task_id}), 202

@api_map_GAN.route('/map-history/<username>', methods=['GET'])
def get_map_history(username):
    try:
        maps = Map.query.filter_by(username=username)\
            .order_by(Map.created_at.desc())\
            .all()
        
        return jsonify({
            'success': True,
            'maps': [{
                'id': map.id,
                'image_url': map.image_url,
                'description': map.description,
                'style': map.style,
                'tone': map.tone,
                'created_at': map.created_at.isoformat()
            } for map in maps]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
