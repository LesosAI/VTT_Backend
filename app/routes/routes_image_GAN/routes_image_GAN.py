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

@api_image_GAN.route('/character-history/<username>', methods=['GET'])
def get_character_history(username):
    try:
        characters = CharacterArt.query.filter_by(username=username)\
            .order_by(CharacterArt.created_at.desc())\
            .all()
        
        return jsonify({
            'success': True,
            'characters': [{
                'id': char.id,
                'image_url': char.image_url,
                'description': char.description,
                'style': char.style,
                'gender': char.gender,
                'created_at': char.created_at.isoformat()
            } for char in characters]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_image_GAN.route('/character/<int:character_id>', methods=['GET'])
def get_character(character_id):
    try:
        character = CharacterArt.query.get(character_id)
        if not character:
            return jsonify({'error': 'Character not found'}), 404
            
        return jsonify({
            'success': True,
            'character': {
                'id': character.id,
                'image_url': character.image_url,
                'description': character.description,
                'style': character.style,
                'gender': character.gender,
                'created_at': character.created_at.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_image_GAN.route('/character/<int:character_id>', methods=['DELETE'])
def delete_character(character_id):
    try:
        character = CharacterArt.query.get(character_id)
        if not character:
            return jsonify({'error': 'Character not found'}), 404
            
        # Verify the user owns this character
        data = request.json
        if character.username != data.get('username'):
            return jsonify({'error': 'Unauthorized'}), 403
            
        db.session.delete(character)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500    