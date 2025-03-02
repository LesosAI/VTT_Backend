from flask import Blueprint, request, jsonify, send_file, make_response, current_app
from app.models.user import CharacterArt, User, db, Tag, Map
import requests
from datetime import datetime
from PIL import Image, ImageDraw
import io
import time
from ...utils.background_tasks import run_in_background, with_app_context, update_task_status

api_image_GAN = Blueprint("api_image_GAN", __name__, url_prefix="/api")

@api_image_GAN.route('/generate-image', methods=['POST'])
def generate_image():
    data = request.json
    username = data.get('username')
    description = data.get('description')
    style = data.get('style')
    gender = data.get('gender')
    tags = data.get('tags', [])  # Get tags from request
    
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
        
        # Add tags
        for tag_name in tags:
            tag = Tag(name=tag_name, character=character_art)
            db.session.add(tag)
            
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
                'created_at': char.created_at.isoformat(),
                'tags': [tag.name for tag in char.tags]
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
                'created_at': character.created_at.isoformat(),
                'tags': [tag.name for tag in character.tags]  # Add tags to response
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

@api_image_GAN.route('/character/<int:character_id>/tags', methods=['POST'])
def add_tag(character_id):
    try:
        data = request.json
        username = data.get('username')
        tag_name = data.get('tag')
        
        character = CharacterArt.query.get(character_id)
        if not character:
            return jsonify({'error': 'Character not found'}), 404
            
        # Verify the user owns this character
        if character.username != username:
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Check if tag already exists
        existing_tag = Tag.query.filter_by(character_id=character_id, name=tag_name).first()
        if existing_tag:
            return jsonify({'error': 'Tag already exists'}), 400
            
        # Create new tag
        tag = Tag(character_id=character_id, name=tag_name)
        db.session.add(tag)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_image_GAN.route('/character/<int:character_id>/tags/<tag_name>', methods=['DELETE'])
def remove_tag(character_id, tag_name):
    try:
        data = request.json
        username = data.get('username')
        
        character = CharacterArt.query.get(character_id)
        if not character:
            return jsonify({'error': 'Character not found'}), 404
            
        # Verify the user owns this character
        if character.username != username:
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Find and delete the tag
        tag = Tag.query.filter_by(character_id=character_id, name=tag_name).first()
        if tag:
            db.session.delete(tag)
            db.session.commit()
            
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_image_GAN.route('/test-background-task', methods=['POST'])
def test_background_task():
    """Test endpoint for background task processing"""
    try:
        data = request.json
        user_id = data.get('username')
        duration = data.get('duration', 15)  # Default 15 seconds
        
        if not user_id:
            return jsonify({'error': 'Username is required'}), 400

        user = User.query.filter_by(username=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Set initial processing state
        update_task_status(user_id, True)
        
        # Start background task
        simulate_long_task(user_id, duration)
        
        return jsonify({
            'message': 'Background task started',
            'status': 'processing',
            'estimated_duration': duration
        }), 202

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)}), 500

@api_image_GAN.route('/task-status/<username>', methods=['GET'])
def get_task_status(username):
    """Get the current processing status for a user"""
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'processing': user.processing,
            'username': user.username
        })

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)}), 500

@run_in_background
@with_app_context
def simulate_long_task(user_id: str, duration: int) -> None:
    """
    Simulate a long-running task with progress updates.
    
    Args:
        user_id: The username of the user
        duration: Task duration in seconds
    """
    try:
        print(f"Starting simulated task for user {user_id}, duration: {duration}s")
        
        # Simulate work
        time.sleep(duration)
        
        # Update status when complete
        update_task_status(user_id, False)
        print(f"Task completed for user {user_id}")
        
    except Exception as e:
        print(f"Error in background task for user {user_id}: {e}")
        update_task_status(user_id, False)

