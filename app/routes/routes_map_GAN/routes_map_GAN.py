from flask import Blueprint, request, jsonify, send_file, make_response
from app.models.user import CharacterArt, User, db, Tag, Map
import requests
from datetime import datetime
from PIL import Image, ImageDraw
import io

api_map_GAN = Blueprint("api_map_GAN", __name__, url_prefix="/api")

@api_map_GAN.route('/generate-map', methods=['POST'])
def generate_map():
    data = request.json
    username = data.get('username')
    description = data.get('description')
    style = data.get('style')
    tone = data.get('tone')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
        
    # For now, using Picsum as a placeholder
    # In production, integrate with your map generation service
    image_url = f"https://picsum.photos/800/600"
    
    # Create new map entry
    map_entry = Map(
        username=username,
        image_url=image_url,
        description=description,
        style=style,
        tone=tone
    )
    
    try:
        db.session.add(map_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'image_url': image_url,
            'id': map_entry.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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
