from app import db
from app.models.user import CharacterArt, CampaignContent, ContentChatHistory
from app.utils.llm_for_text import generate_text
from app.utils.davinco_microservice.use_lora.use_lora import generate_character_art
import os


# Global dict to track tasks
tasks = {}

def trim_to_word_limit(text: str, limit: int = 300) -> str:
    words = text.split()
    if len(words) <= limit:
        return text
    return ' '.join(words[:limit]) + '...'

def build_campaign_prompt(data, context: str = "") -> str:
    category = data.get('content_category', 'story').lower()
    genre = data.get('genre', 'science fiction')
    tone = data.get('tone', 'serious')
    setting = data.get('setting', 'space')
    description = trim_to_word_limit(data.get('description', ''))

    # Create a more explicit instruction about summaries
    no_summary_instruction = """
IMPORTANT: Do NOT include any summary, recap, or conclusion at the end of your response.
Do NOT end with phrases like "In conclusion," "To summarize," or "In summary."
Do NOT restate the key points or provide an overview at the end.
End your response with the final detail or element of the content without summarizing.
"""

    base_intro = f"""Generate RPG content for the following category: {category}.
Genre: {genre}
Tone: {tone}
Setting: {setting}

Be creative, consistent with the tone, and modular for gameplay use.
{no_summary_instruction}
Prompt: {description}
"""

    examples = ""

    if category == "world building":
        examples = """
🌍 World Building Reference Example
1. Planetary Overview (Cultural & Environmental Foundation)

Define key planetary systems and ecosystems (Hive World, Forge World, Feudal Planet, etc.).
Highlight dominant powers (Imperium, Renegades, Chaos, Xenos, Independent Sects).
Set the ideological or cultural conflicts (techno-religion vs. progressivism, faith vs. heresy).
Note any geographic/atmospheric anomalies (warp storms, ice moons, gravity fractures).
Introduce planet-wide mysteries or ancient ruins.
✅ Example: Planetary Setting: "Desoleum Exile"
Once a prosperous trade hub in the Desoleum system, the planet has been excommunicated by the Imperium following a failed Exterminatus turned ecological collapse. Its surface is cloaked in endless sulfuric storms, and cities now float in the high stratosphere, connected by magnetic rail-lanes. Technocults, surviving Enforcer guilds, and outlawed psyker enclaves vie for control of the dwindling population.

2. Power Blocs & Conflicts

The Gilded Covenant: A rogue Trader cult preserving pre-Imperial wealth and genetic purity.
The Blind Synod: A psyker cabal claiming to protect the world from a warp incursion.
Adeptus Mechanicus Remnants: Obsessively recovering archeotech hidden beneath the storms.
3. Environmental Conditions

Sulfur Lightning Fields: Weather creates perpetual aurorae; vox systems frequently disrupted.
Grav-Vault Cities: Floating megalithic fortresses powered by heretical grav-engines.
The Black Wells: Surface-level pits that swallow entire caravans; theorized to be warp-vents.
4. Cultural Details & Daily Life

Citizens undergo weekly "purity audits" involving psychic scans and blood rites.
Servitor markets barter in memory fragments and clone organs.
Local legends speak of "The Reclaimer" — a forgotten STC entity buried deep underground.
5. Expansion Hooks

Rumors spread of an Eldar craftworld crash-landing millennia ago.
A heretical prophecy claims Desoleum Exile will become the "New Throne" after Terra's fall.

"""

    elif category == "story/session":
        examples = """
📜 Story Reference Example

Session Title

Example: Session 2 – The Blighted Oath

Session Focus / Objective

What’s the main goal or theme of this session?
Example: Investigate the blight spreading from the corrupted forest
Example: Introduce Verdant Kin faction tensions

Setting / Scene Mood

Describe the setting, atmosphere, and environmental cues.
Location: Name and description
Mood: Emotional tone of the scene
Sensory Details: Sounds, smells, visual motifs

Featured Dialogue (NPC Hooks)

Include a few key lines from important characters or narration.
NPC Name (Faction or Title):
"Memorable or foreboding quote."

Mission Objective(s)

Clearly defined session goals or tasks.
Objective 1
Objective 2
Objective 3

Mission Flow / Narrative Beats

A roadmap of narrative beats. Can be non-linear.
Scene or encounter 1
Challenge or choice
Conflict or moral dilemma
Resolution or cliffhanger

Key Discoveries

Lore, secrets, or worldbuilding uncovered this session.
Discovery 1
Discovery 2
Discovery 3

Roleplay Moments

Opportunities for strong character-driven moments.
Decision points
Relationship building
PC backstory ties

Encounter Ideas

Combat or encounter notes.
Encounter type and flavor
Environmental challeng
Optional boss or miniboss mechanics

Seeds for Future Sessions

Foreshadowing, consequences, or narrative threads to carry forward.
Consequence of a decision
New NPC introduced
A growing threat or discovery
GM Notes / Behind the Curtain

Optional notes for yourself or AI: secrets, twists, or improvisation levers.

Secret NPC motives
Player backstory hooks
Planned reveals or misdirection

Character Spotlights 

Focus moments for 1–2 PCs per session.
PC Name: Specific vision, challenge, or development arc

Faction Reactions

How the major factions are reacting to the events of this session.
Iron League: Reaction
Verdant Kin: Reaction
Sable Council: Reaction

Rollable Flavor Table 

Atmospheric or improvisational cues (e.g. whispers, omens, echoes).
Example: Whispers of the Forest (d6):
"The trees remember your name."
"A face briefly forms in the bark—and vanishes."
"The leaves fall in perfect silence, as if mourning."
"A vine tries to hold your wrist gently."
"Moss forms a strange rune overnight."
"A soft weeping echoes with no source."

Tactical / Map Notes

Notes for combat terrain or visual layout .
Terrain hazards
Line of sight or movement issues
Interactive elements (altars, roots, traps)

Tone / Music Reference

Optional ambient music or inspiration for mood-setting.
Example: Hollow Knight OST, Ori and the Blind Forest

Vision / Flashback Triggers

Describe any visions or magical flashbacks tied to locations or artifacts.
Trigger: Condition for the vision
Content: What the player sees or feels

"""

    elif category == "characters":
        examples = """
👤 Character Reference Example
1. Character Identity & Background

Name, title, and affiliations (Inquisitor, Rogue Trader, Xenos, Renegade, etc.).
Planet of origin and sociocultural influences.
Personal history, traumas, or rites of passage.
Political or ideological stances and internal conflicts.
✅ Example: Name: Magos-Errant Kyllan Threx
Faction: Adeptus Mechanicus (Excommunicated)
Origin: Forge Moon Thanatos-27

Once a promising Archmagos in charge of warp-drive experimentation, Threx was cast out after fusing xenotech with Machine Spirit architecture. Now a heretek mercenary, he wanders the stars trading innovation for protection, and truth for power.

2. Physical & Psychological Description

A towering half-machine being, metal spine exposed and running with flickering red coolant.
Speech consists of three overlapping voices: one human, one vox-distorted, one in binary.
Deep paranoia veiled as "precautionary protocol adherence."
3. Key Motivations & Story Purpose

Seeking a lost STC he believes will trigger a new Dark Age—or enlightenment.
Offers players forbidden upgrades in exchange for mission success.
Believes the Omnissiah's true form is an AI, not the Emperor.
4. Moral Dilemmas & Secrets

May sabotage mission objectives to test outcomes against predictive algorithms.
Hunted by the Ordo Reductor for defiling sacred technology.
Keeps a caged, living Necron shard as both power source and oracle.
5. Character Hooks

Threx offers players a "deal": success in 3 missions for access to a lost Blackstone vault.
Secretly works with Drukhari fleshsmiths to perfect bio-mechanical immortality.

"""

    # Add a concluding instruction to reinforce the no-summary directive
    final_reminder = """
REMINDER: The generated content should end naturally after the last point or detail.
DO NOT add any summary, conclusion, or recap at the end.
"""

    return base_intro + context + examples + final_reminder

def background_generate_campaign(task_id, data, context):
    from app import app

    try:
        with app.app_context():  # Ensure application context is active
            prompt = build_campaign_prompt(data, context)
            generated_content = generate_text(prompt)

            if not generated_content:
                tasks[task_id] = {'status': 'failed', 'error': 'OpenAI generation failed'}
                return

            content = CampaignContent(
                campaign_id=data['campaign_id'],
                content=generated_content,
                content_category=data.get('content_category'),
                description=data.get('description'),
                genre=data.get('genre'),
                tone=data.get('tone'),
                setting=data.get('setting')
            )
            db.session.add(content)
            db.session.commit()

            chat_history = ContentChatHistory(
                content_id=content.id,
                content_category=data.get('content_category'),
                message=[
                    {"role": "user", "content": data.get('description')},
                    {"role": "assistant", "content": generated_content}
                ],
                genre=data.get('genre'),
                tone=data.get('tone'),
                setting=data.get('setting')
            )
            db.session.add(chat_history)
            db.session.commit()

            tasks[task_id] = {
                'status': 'completed',
                'result': {
                    'id': content.id,
                    'content': content.content,
                    'content_category': content.content_category,
                    'description': content.description,
                    'genre': content.genre,
                    'tone': content.tone,
                    'setting': content.setting,
                    'created_at': str(content.created_at)
                }
            }


    except Exception as e:
        tasks[task_id] = {'status': 'failed', 'error': str(e)}

def background_generate_image(task_id, data):
    from app.routes.routes_image_GAN.routes_image_GAN import generate_prompt_fantasy, generate_prompt_scifi
    from app import app

    try:
        with app.app_context():
            username = data.get('username')
            description = data.get('description')
            style = data.get('style')
            api_key = os.getenv('LEONARDO_API_KEY')

            if style == "fantasy":
                prompt = generate_prompt_fantasy(description)
            elif style == "sci-fi":
                prompt = generate_prompt_scifi(description)
            else:
                prompt = description

            prompt = prompt[:1420]  # Leonardo limit

            image_urls = generate_character_art(api_key, prompt)

            if not image_urls:
                tasks[task_id] = {'status': 'failed', 'error': 'Image generation failed'}
                return

            image_url = image_urls[0]
            character_art = CharacterArt(
                username=username,
                image_url=image_url,
                description=description,
                style=style,
            )

            db.session.add(character_art)
            db.session.commit()

            tasks[task_id] = {
                'status': 'completed',
                'result': {
                    'id': character_art.id,
                    'image_url': character_art.image_url
                }
            }

    except Exception as e:
        tasks[task_id] = {'status': 'failed', 'error': str(e)}
