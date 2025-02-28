from flask import Blueprint, request, jsonify
from app.models.user import CharacterArt, User, db
import requests
from datetime import datetime

api_image_GAN = Blueprint("api_image_GAN", __name__, url_prefix="/api")

@api_image_GAN.route('/generate-image', methods=['POST'])
def generate_image():
    data = request.json
    username = data.get('username')
    description = data.get('description')
    style = data.get('style')
    gender = data.get('gender')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
        
    # For now, we'll use Picsum as a placeholder
    # In a real implementation, you'd integrate with your actual image generation service
    image_url = f"https://picsum.photos/800/600"
    
    # Create new character art entry
    character_art = CharacterArt(
        username=username,
        image_url=image_url,
        description=description,
        style=style,
        gender=gender
    )
    
    try:
        db.session.add(character_art)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'image_url': image_url,
            'id': character_art.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500    