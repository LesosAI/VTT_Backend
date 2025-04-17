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

    # Species-specific context
    species_context = {
        "tabaxi": "Feline humanoids with sleek fur, sharp claws, and an agile build. Known for their curiosity, speed, and nomadic lifestyle. Their features blend jungle cat elegance with tribal mystique.",
        "firbolg": "Gentle forest giants, with mossy skin and glowing blue eyes. They revere nature, wield druidic magic, and act as hidden guardians of the woods.",
        "dragonborn": "Proud, draconic humanoids with scaled skin and a breath weapon tied to their lineage. Their culture is steeped in honor and ancient legacy."
    }

    # Inject species lore if found
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
    # Instructions to ChatGPT
    instructions = (
        "You are a fantasy concept artist's AI assistant. "
        "Given a brief character description, generate a rich, visual prompt for AI image generation in Leonardo.Ai. "
        "Use vivid detail, imaginative fantasy elements, physical traits, clothing, and setting. "
        "The character must have a realistic number of limbs, eyes, and fingers. "
        "Do NOT exceed 1350 characters. "
        "End with: 'Use cinematic perspective with natural camera framing to emphasize mood, depth, and detail.'"
    )

    fantasy_style = (
        "ultra-detailed, cinematic lighting, atmospheric depth, highly dynamic pose, "
        "photo-realistic textures, flowing fabrics, intricate armor, ornate accessories, "
        "4K, sharp focus, dramatic shadows, golden hour or moody lighting, majestic scenery, "
        "dust particles, volumetric fog, epic background, stylized realism"
    )

    # Compose final GPT prompt
    final_prompt = (
        f"{instructions}\n\n"
        f"User description: \"{description}\"\n\n"
        f"Examples:\n{example_prompts}\n\n"
        f"Prompt settings:\n{fantasy_style}\n\n"
        f"Generate the final prompt below:\n"
    )
    prompt = generate_text(final_prompt)
    return prompt

def generate_prompt_scifi(description):

    # Sci-fi flavored context for shared species
    species_context = {
        "tabaxi": (
            "Feline humanoids adapted to high-gravity frontier worlds, renowned for stealth, speed, and cyber-reflexes. "
            "Often serve as scouts, infiltrators, or rogue tech-thieves with sleek fur and digitigrade legs."
        ),
        "firbolg": (
            "Massive, bio-engineered forest dwellers from terraformed green worlds. "
            "Use empathic powers and symbiotic plant-cybernetics, often healers or eco-hackers deep in biozones."
        ),
        "dragonborn": (
            "Draconic humanoids from irradiated wastelands and forge-worlds, with scale-armored skin, plasma breath, and ancient warrior codes. "
            "Serve as shock troopers, warlords, or emissaries from lost dynasties."
        )
    }

    lowered = description.lower()
    for species, context in species_context.items():
        if species in lowered:
            description += f" ({context})"
            break


    example_prompts = """
    Prompt 1:       


A tall, slender Drukhari Archon sits on an elevated throne forged from blackened bone and polished metal blades. He wears intricately crafted obsidian-black armor with crimson and silver trim, adorned with barbed filigree and etched symbols. Spiked pauldrons arc outward with delicate chains draped between them, holding trophies like rings and bones. A dark crimson cloak, lined with shimmering silk and shifting patterns of screaming faces, cascades down the throne steps. His pale, gaunt face has sharp, aristocratic features with crimson glowing eyes and long, jet-black hair streaked with silver, braided with bone charms. His lips curl into a sardonic smirk. In his right hand, he lazily holds a barbed agoniser whip; his left rests on the hilt of a rune-etched blade. The background is a dark throne room with twisted black wraithbone pillars, flayed banners, and faint violet and crimson lighting. Chains and soul-cages hang from the ceiling, and the air is filled with red smoke and flickering soul-lights, evoking menace and dark elegance.

    Prompt 2:

A Drukhari Wych stands poised in a lethal combat stance within a blood-soaked arena of Commorragh. Her lithe, muscular frame is adorned with sleek, form-fitting armor of dark crimson and obsidian black, trimmed with jagged silver edges. Her armor leaves her limbs exposed for agility, displaying scars from countless battles. Wicked, curved blades are attached to her wrists, gleaming under the arena's soul-light torches. Her face is partially hidden behind an ornate mask with sharp angular designs, and her piercing, predatory eyes glow with a sinister green hue. Dark hair, streaked with pale silver, flows freely behind her as she moves. The ground beneath her is cracked and stained with old blood, scattered with broken weapons and bones. Spiked metal walls encircle the arena, with shadowy Drukhari spectators watching from the stands, their outlines illuminated by flickering purple flames. Chains and hooks hang ominously above, while green mist swirls along the ground, adding to the scene’s dangerous and electrifying atmosphere.

    Prompt 3:
    
An ancient, half-dead figure sat enthroned atop a pile of decaying data-slates, cracked scrolls, and rusted cogitator cores. His bloated, cybernetic body is heavily augmented, hunched forward and partially fused into a vast, gothic cogitator array that surrounds him like a mechanical throne. His torso is adorned with fading cog-mechanicus symbols, exposed cabling, and layered circuits. Dozens of mechadendrites emerge from his back like a tangle of mechanical tentacles, some plugged directly into data terminals, others idly twitching as if searching for more information to consume. His arms are elongated and skeletal, permanently fused into ancient data-scroll readers and spinning memory-core spindles. His face is withered flesh with only remnants of bone remaining, encased in a cracked rebreather mask. One glowing bionic eye glows red with cold logic; the other socket leaks sacred machine-oil, trailing down his face. His lips are pulled back in a rictus sneer, and his mouth murmurs fragmented binary litanies. Around his throne, faded banners hang from servo-cranes, displaying forgotten Mechanicus designations. Dim, flickering cogitator screens glow in the background, filled with scrolling, corrupted data code. The lighting is cold and sterile, casting deep shadows across the throne and highlighting the ancient, inhuman presence of the Dominus.

Prompt 4:

A massive, corrupted medical servitor stands in the center of a decayed Adeptus Mechanicus hospital ship. Once a battlefield triage unit, it now harvests instead of heals. Its towering frame is reinforced with battle-worn plating, covered in rust, dried blood, and faded cog-mechanicus sigils. Its featureless faceplate has a single flickering red optic, scanning with eerie precision, while its exposed lower jaw reveals stitched flesh and grotesque vocal augments that distort its speech into garbled binary and mechanical whispers. A nightmarish array of surgical appendages twitches with malicious intent. Whirring bone saws, arterial extractors, and fluid injectors filled with unknown substances calibrate automatically, each tool designed for life-saving procedures now repurposed for something far worse. One oversized manipulator claw, once used to stabilize patients, now grips with bone-crushing force. Its reinforced exoskeleton is riddled with leaking tubes pumping virulent green fluids, leaving sickly trails of oil and organic matter in its wake. One arm wields a rusted, bloodstained surgical saw, while another flexes a long, serrated injector filled with an unknown concoction. The atmosphere is sterile horror, where once-sacred technology has become a nightmare of clinical detachment and mechanical dread.

    Prompt 5:
    Captain Ellara Venn, a Warhammer 40k Rogue Trader, exudes authority and alluring sensuality. She wears a navy blue coat with gold filigree, a crimson-lined interior, and a corset-like black leather bodice adorned with silver runes. Her crimson sash, pinned with a ruby-encrusted aquila seal, complements her sleek navy trousers and gilded knee-high boots. A Gothic steel pauldron with sigils and a golden epaulet enhance her commanding presence. She carries an ornate power saber with a skull motif and a plasma pistol, with a crystal-tipped cane in one hand. Her golden hair flows in waves, framing her porcelain skin, sharp almond-shaped eyes, and a faint scar on her cheekbone. Set on a starship's dimly lit, Gothic-style command deck, with brass pipes and glowing panels, her presence is regal and foreboding.


    """
# GPT instructions
    instructions = (
        "You are a prompt engineer for AI image generation based on high-fidelity sci-fi character art. "
        "Based on the description, craft a highly imaginative and cinematic prompt suitable for Leonardo.Ai. "
        "Use rich detail, technology, atmosphere, attire, and dramatic setting. Always reflect elements from the Warhammer 40K universe for tone and depth. "
        "Do NOT exceed 1350 characters "
        "Ensure the character has the correct number of limbs, eyes, and fingers. "
        "End the prompt with: 'Use cinematic perspective with natural camera framing to emphasize mood, depth, and detail.'"
    )

    scifi_style = (
        "sci-fi ultra-detail, neon reflections, biomechanical textures, cinematic cyberpunk lighting, "
        "4K resolution, gritty or sterile futuristic environments (like starships, megacities, alien ruins), "
        "realistic materials, glowing holograms, tactical gear, rain, smoke, HDR contrast, chromatic aberration"
    )

    # Final input for ChatGPT
    final_prompt = (
        f"{instructions}\n\n"
        f"User description: \"{description}\"\n\n"
        f"Example prompts:\n{example_prompts}\n\n"
        f"Prompt settings:\n{scifi_style}\n\n"
        f"Now write the final prompt below:\n"
    )    

    prompt = generate_text(final_prompt)

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
        negative_prompt = "blurry, extra limbs, malformed hands, extra fingers, disfigured face, low quality, poorly drawn, deformed, glitch, cartoon, disjointed anatomy, cropped, signature, text"
        
    elif style == "sci-fi":
        prompt = generate_prompt_scifi(description)
        negative_prompt = "blurry, extra limbs, deformed hands, extra fingers, double head, disfigured, low detail, poor anatomy, surreal, abstract, glitchy, cartoonish, cropped, watermarked, text, signature"
        
    else:
        prompt = description
    print(prompt)

    if len(prompt) > 1420:
        prompt = prompt[:1420]


    # prompt= f"Ensure you have the correct number of limbs and eyes, and the correct number of limbs, and the correct number of eyes {prompt}"
    # Generate image using Leonardo AI with the description
    image_urls = generate_character_art(api_key, prompt, negative_prompt)
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

