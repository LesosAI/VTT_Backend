from flask import Blueprint, request, jsonify, send_file, make_response
from app.models.user import CharacterArt, User, db
import requests
from datetime import datetime
from PIL import Image, ImageDraw
import io

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

@api_image_GAN.route('/character/<int:character_id>/token', methods=['GET'])
def get_character_token(character_id):
    try:
        character = CharacterArt.query.get(character_id)
        if not character:
            return jsonify({'error': 'Character not found'}), 404
            
        # Download original image
        response = requests.get(character.image_url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to download image'}), 500
            
        img = Image.open(io.BytesIO(response.content))
        
        # Make the image square
        min_dim = min(img.width, img.height)
        left = (img.width - min_dim) // 2
        top = (img.height - min_dim) // 2
        img = img.crop((left, top, left + min_dim, top + min_dim))
        
        # Resize to standard token size
        size = 1200
        img = img.resize((size, size))
        
        # Create circular mask
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        
        # Create output image with transparency
        output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        output.paste(img, (0, 0))
        output.putalpha(mask)
        
        # Add frame
        draw = ImageDraw.Draw(output)
        frame_width = 15
        frame_color = (139, 69, 19)  # Brown frame
        draw.ellipse((0, 0, size-1, size-1), outline=frame_color, width=frame_width)
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        output.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        response = make_response(send_file(
            img_byte_arr,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'character-{character_id}-token.png'
        ))
        
        # Add CORS headers
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500    