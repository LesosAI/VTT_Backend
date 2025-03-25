from flask import Blueprint, request, jsonify, send_file, make_response, current_app
from app.models.user import CharacterArt, User, db, Tag, Map
import requests
from datetime import datetime
from PIL import Image, ImageDraw
import io
import time
import os
from app.utils.davinco_microservice.use_lora.use_lora import generate_character_art
from app.utils.llm_for_text import generate_text
api_image_GAN = Blueprint("api_image_GAN", __name__, url_prefix="/api")



def generate_prompt_fantasy(description):
    example_prompts = """
    
    Prompt 1:       

Create an image of a serene monk exuding an aura of tranquility, yet possessing the ability to control the winds with a mere gesture. The monk's robes billow around him as if caught in a perpetual breeze, emphasizing his connection to the element of air. His eyes are closed in deep concentration, with wisps of wind swirling around his outstretched hand. In the background, a mystical temple shrouded in mist and surrounded by ancient trees adds an air of mystery and magic to the scene.

    Prompt 2:

Create an image of a cool monk in a fantasy setting, exuding an aura of mysticism and wisdom. The monk is dressed in flowing robes adorned with intricate patterns, and is holding a staff with a glowing crystal at the top. His eyes are sharp and focused, hinting at hidden knowledge and power. The background is a misty forest filled with ancient trees and magical creatures, with shafts of golden light filtering through the canopy above, creating an atmosphere of enchantment and tranquility

    Prompt 3:
    
Create an image of an albino assassin in a fantasy world, with pale skin, white hair, and piercing red eyes. The assassin is dressed in sleek, black leather armor, adorned with intricate silver patterns. They are holding a deadly, curved blade with a glowing blue gem embedded in the hilt. The background is a shadowy alleyway, illuminated by the soft glow of a distant street lamp, casting long, ominous shadows.
        
    """
    prompt = f"Generate a prompt for a fantasy character based on this description: {description}. Use the following examples as a reference: {example_prompts}"
    prompt = generate_text(prompt)
    return prompt

def generate_prompt_scifi(description):
    example_prompts = """
    Prompt 1:       

Create an image of a stoic and battle-hardened Librarian of the Blood Angels chapter, emanating an aura of psychic dominance and war-forged wisdom. His crimson power armor, adorned with glowing gold runes of protection, stands as a testament to his mastery of the arcane arts. His psychic hood hums faintly with suppressed energy, while his gaunt face, etched with deep scars, reveals cold, unyielding eyes that glow with sapphire light. The air around him shimmers with latent psychic power, distorting the space near his outstretched hand. In the background, a war-ravaged cathedral with shattered stained glass and flickering braziers evokes a sense of grim reverence and somber resolve.

Negative Prompts:

No casual modern clothing

No anime or cartoonish features

No neon cyberpunk elements

No superhero-style stances

    Prompt 2:

Create an image of a relentless and unyielding Inquisitor, draped in a heavy, dark leather coat lined with iron clasps and reinforced plates. His steely gaze pierces through the gloom, cold and calculating. A silver-topped staff, engraved with intricate sigils of purity, crackles faintly with divine energy as he channels his unshakable will. Chains bearing the emblems of the Emperor drape across his chest, while a battered tome of forbidden knowledge hangs from his belt. The scorched ruins of a heretic temple smolder behind him, embers dancing in the air like fleeting spirits of the damned.

Negative Prompts:

No casual modern clothing

No anime or cartoonish features

No neon cyberpunk elements

No superhero-style stances

    Prompt 3:
    
Create an image of a solemn Battle Priest, clad in fur-lined armor crusted with frost and rimed with ice. His long, silver beard flows beneath a heavy hood embroidered with symbols of sacred power. In his gloved hands, he wields an ancient warhammer, its head sculpted like a snarling wolf, crackling with frozen energy. Cold mist curls around his boots as the frozen wind howls through a desolate mountain pass behind him. His calm, resolute expression suggests a spirit forged in hardship and tempered by unwavering faith.

Negative Prompts:

No casual modern clothing

No anime or cartoonish features

No neon cyberpunk elements

No superhero-style stances
    
    
    """
    prompt = f"Generate a prompt for a scifi character based on this description: {description}. Use the following examples as a reference: {example_prompts}"
    prompt = generate_text(prompt)
    return prompt


@api_image_GAN.route('/generate-image', methods=['POST'])
def generate_image():
    data = request.json
    username = data.get('username')
    description = data.get('description')
    style = data.get('style')

    
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    # Get Leonardo API key from environment
    api_key = os.getenv('LEONARDO_API_KEY')
    if not api_key:
        return jsonify({'error': 'Leonardo API key not configured'}), 500

    if style == "fantasy":
        prompt = generate_prompt_fantasy(description)
    elif style == "scifi":
        prompt = generate_prompt_scifi(description)
    else:
        prompt = description
    print(prompt)

    # Generate image using Leonardo AI with the description
    image_urls = generate_character_art(api_key, prompt)
    if not image_urls:
        return jsonify({'error': 'Failed to generate image'}), 500

    image_url = image_urls[0]  # Take the first generated image
    print(image_url)
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

