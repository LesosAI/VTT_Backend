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

    # Add species-specific context
    species_context = {
        "tabaxi": "They are feline humanoids with sleek fur, sharp claws, and an agile build. Known for their curiosity, speed, and nomadic lifestyle. Their features blend jungle cat elegance with tribal mystique.",
        "firbolg": "They are gentle forest giants, standing tall with mossy skin and glowing blue eyes. They revere nature, wield druidic magic, and often serve as hidden guardians of the woods.",
        "dragonborn": "They are proud, draconic humanoids with scaled skin, strong physiques, and a breath weapon tied to their ancestral lineage. Their culture is steeped in honor and legacy."
    }

    # Normalize and inject context if species is mentioned
    lowered = description.lower()
    for species, context in species_context.items():
        if species in lowered:
            description += f" ({context})"
            break

    example_prompts = """
    
    Prompt 1:       

a tall and weathered guardian standing at the edge of a scorched forest where
blackened trees meet a smoldering plain. His bare arms are crisscrossed with
glowing ember-orange runes that pulse faintly beneath cracked, ash-covered
skin. He wears a mantle of ironwood bark layered over soot-streaked leather
armor, a massive curved blade slung across his back, still radiating heat from
recent battle. The sky is dim with drifting smoke, pierced by shafts of amber light
filtering through the haze. The ground is charred and broken, with embers
glowing in the crevices, and the air shimmers faintly from residual heat. His
expression is grim and resolute as he surveys the horizon, smoke curling around
him like a cloak. Use cinematic perspective with natural camera framing to
emphasize mood, depth, and detail.


    Prompt 2:

Bone-Seer of Hollowmere, a blind oracle standing at the edge of a mist-laden
swamp beneath a canopy of gnarled, leafless trees. Her face is calm and
expressionless, with polished bone marbles in place of eyes, faintly etched with
ancient glyphs. Draped in tattered raven feathers and a shawl of stitched animal
hides, she clutches a ritual blade carved from ivory and a satchel of jangling
charm-bones that whisper in the silence. Pale mist coils around her bare feet as
she walks across a slick wooden platform half-sunken into the muck. Ghostly
shapes flicker in the fog behind her, drawn by her presence. The lighting is dim
and cold, filtered through hanging moss and faint moonlight, casting elongated
shadows across her figure. The texture of damp wood, bone, and feathers
contrasts with the spectral glow in her hollow gaze. The mood is eerie and
prophetic, filled with the weight of unseen watchers. Use cinematic perspective
with natural camera framing to emphasize mood, depth, and detail.


    Prompt 3:
    
Thornbound Knight, a solemn warrior standing in a fog-choked grove of dying
trees, his form wrapped in splintered, moss-covered armor dulled by time and
sorrow. Twisting brambles crown his brow, growing from his skull in a living halo
of thorns that pierce his flesh, a symbol of his eternal penance. His face is pale
and resolute, eyes shadowed beneath a battered helm slung to his side. He grips
a weathered longsword etched with faded holy script, its blade stained by blood
and sap alike. Golden banners hang torn from his back, trailing into the mist like
memories of glory. The air is still and damp, filled with the faint scent of rot and
wet earth, as diffuse silver light breaks through the canopy in shafts that shimmer
with drifting spores. The ground is soft with fallen leaves and old petals, some
caught in the brambles growing from his armor. The emotional tone is one of
quiet suffering and grim nobility. Use cinematic perspective with natural camera
framing to emphasize mood, depth, and detail.


    Prompt 4:

Vulture Alchemist, a hunched and wiry figure skulking through the edge of a
battlefield at dusk, scavenging among broken weapons and scorched earth. His
patchwork leather coat is stained with blood and alchemical burns, adorned with

feathers, bones, and stitched sigils. Thick goggles made from polished vulture
bones magnify his sunken eyes, and a crooked grin stretches beneath a beaked
mask hanging loosely from his neck. Slung across his back are clinking glass
vials, bundles of herbs, and a tattered satchel bulging with unholy concoctions.
He kneels beside a fallen soldier, extracting something glimmering into a vial that
pulses with sickly green light. The setting sun casts a bruised orange hue over
the smoke-laced sky, while distant crows wheel and scream overhead. The
ground is cracked and littered with corpses, alchemical residue, and twitching
plants fed by unnatural toxins. The air shimmers with volatile fumes, and faint
sparks dance around his gauntleted hands. The mood is macabre yet
methodical, steeped in grim curiosity. Use cinematic perspective with natural
camera framing to emphasize mood, depth, and detail.

    """
    general_instructions = "must be a fantasy character, with the correct number of limbs, and the correct number of eyes, and the correct number of fingers.  ENSURE THE OUTPUT IS BELLOW 250 WORDS, ENSURE THE OUTPUT IS BELLOW 250 WORDS"

    prompt = f"Generate a prompt for a fantasy character STRICTLY within 1350 CHARACTERS based on this description: {description}. Please use the following general instructions: {general_instructions}. Use the following examples as a reference: {example_prompts}"
    prompt = generate_text(prompt)
    return prompt

def generate_prompt_scifi(description):

    # Sci-fi flavored context for shared species
    species_context = {
        "tabaxi": (
            "They are feline humanoids adapted to high-gravity frontier worlds, known for agility, stealth, and sharp reflexes. "
            "Often serving as scouts, infiltrators, or rogue tech-thieves, they have sleek fur, enhanced senses, and flexible digitigrade legs."
        ),
        "firbolg": (
            "They are massive bio-engineered forest dwellers from terraformed arboreal planets. "
            "Possessing empathic abilities and plant-symbiotic cybernetics, they act as healers, guardians, or eco-hackers in deep green zones."
        ),
        "dragonborn": (
            "They are proud, draconic humanoids from irradiated wastelands or forge-worlds. "
            "Known for their scale-armored skin, plasma breath, and a culture steeped in ancient war-rites, they often serve as elite shock troopers or honor-bound emissaries."
        )
    }

    lowered = description.lower()
    for species, context in species_context.items():
        if species in lowered:
            description += f" ({context})"
            break


    example_prompts = """
    Prompt 1:       

Long-dead figure standing amidst the ruins of a derelict voidship throne room. He
wears rusted, once-regal golden armor, now corroded and battle-worn, with a
shattered Aquila emblazoned on his chest—one wing missing, the other
scorched and twisted. His face is half-decayed, revealing dry bone beneath
peeling flesh, yet he remains animate, his expression solemn and distant. His
movements appear glitched and fragmented, as though trapped in overlapping
timelines, flickering slightly out of sync with reality. He clutches a broken signet
ring in his right hand, its crest matching the symbol etched onto a crumbling
Warrant of Trade at his feet. Warp-light spills through a shattered viewing window
behind him, casting eerie violet and blue hues across the fractured marble floor
and drifting motes of dust. The air crackles with static interference and residual
energy, and faint ghost-images of alternate versions of the figure briefly phase
around him—remnants of fractured time. Set the atmosphere to feel heavy with
sorrow, grandeur, and haunting decay, evoking a lost legacy corrupted by the
passage of time and exposure to the warp.

    Prompt 2:

A tall, slender Drukhari Archon sits on an elevated throne forged from blackened
bone and polished metal blades. He wears intricately crafted obsidian-black
armor with crimson and silver trim, adorned with barbed filigree and etched
symbols. Spiked pauldrons arc outward with delicate chains draped between
them, holding trophies like rings and bones. A dark crimson cloak, lined with
shimmering silk and shifting patterns of screaming faces, cascades down the
throne steps. His pale, gaunt face has sharp, aristocratic features with crimson
glowing eyes and long, jet-black hair streaked with silver, braided with bone
charms. His lips curl into a sardonic smirk. In his right hand, he lazily holds a
barbed agoniser whip; his left rests on the hilt of a rune-etched blade. The
background is a dark throne room with twisted black wraithbone pillars, flayed
banners, and faint violet and crimson lighting. Chains and soul-cages hang from
the ceiling, and the air is filled with red smoke and flickering soul-lights, evoking
menace and dark elegance.

    Prompt 3:
    
A Drukhari Wych stands poised in a lethal combat stance within a blood-soaked
arena of Commorragh. Her lithe, muscular frame is adorned with sleek, form-
fitting armor of dark crimson and obsidian black, trimmed with jagged silver
edges. Her armor leaves her limbs exposed for agility, displaying scars from
countless battles. Wicked, curved blades are attached to her wrists, gleaming
under the arena&#39;s soul-light torches. Her face is partially hidden behind an ornate
mask with sharp angular designs, and her piercing, predatory eyes glow with a

sinister green hue. Dark hair, streaked with pale silver, flows freely behind her as
she moves. The ground beneath her is cracked and stained with old blood,
scattered with broken weapons and bones. Spiked metal walls encircle the
arena, with shadowy Drukhari spectators watching from the stands, their outlines
illuminated by flickering purple flames. Chains and hooks hang ominously above,
while green mist swirls along the ground, adding to the scene’s dangerous and
electrifying atmosphere.

Prompt 4:

A tall, slender Drukhari Archon sits on an elevated throne forged from blackened
bone and polished metal blades. He wears intricately crafted obsidian-black
armor with crimson and silver trim, adorned with barbed filigree and etched
symbols. Spiked pauldrons arc outward with delicate chains draped between
them, holding trophies like rings and bones. A dark crimson cloak, lined with
shimmering silk and shifting patterns of screaming faces, cascades down the
    
EACH PROMPT GENERATION MUST INCLUDE INSPIRED BY THE SETTING OF WARHAMMER 40K
    """
    prompt = f"Generate a prompt for a scifi character STRICTLY within 1350 CHARACTERS based on this description: {description}. Use the following examples as a reference: {example_prompts}"
    prompt = generate_text(prompt)
    return prompt


@api_image_GAN.route('/generate-image', methods=['POST'])
def generate_image():
    data = request.json
    username = data.get('username')
    description = data.get('description')
    style = data.get('style')

    print(style)
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    # Get Leonardo API key from environment
    api_key = os.getenv('LEONARDO_API_KEY')
    if not api_key:
        return jsonify({'error': 'Leonardo API key not configured'}), 500

    if style == "fantasy":
        prompt = generate_prompt_fantasy(description)
    elif style == "sci-fi":
        prompt = generate_prompt_scifi(description)
    else:
        prompt = description
    print(prompt)

    if len(prompt) > 1420:
        return prompt[:1420]


    # prompt= f"Ensure you have the correct number of limbs and eyes, and the correct number of limbs, and the correct number of eyes {prompt}"
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
    )
    
    try:
        db.session.add(character_art)
        
        # Add tags
            
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

