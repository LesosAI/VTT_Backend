from flask import Blueprint, request, jsonify
from app.models.user import Campaign, CampaignContent, CharacterArt, Map, db
from datetime import datetime
from app.utils.llm_for_text import generate_text

api_campaign_GAN = Blueprint("api_campaign_GAN", __name__, url_prefix="/api")


@api_campaign_GAN.route('/campaigns/<username>', methods=['GET'])
def get_campaigns(username):
    campaigns = Campaign.query.filter_by(username=username).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'created_at': str(c.created_at)
    } for c in campaigns])

@api_campaign_GAN.route('/campaigns', methods=['POST'])
def create_campaign():
    data = request.json
    if not data.get('name') or not data.get('username'):
        return jsonify({'error': 'Name and username are required'}), 400
        
    campaign = Campaign(
        name=data['name'],
        username=data['username']
    )
    
    try:
        db.session.add(campaign)
        db.session.commit()
        return jsonify({
            'id': campaign.id,
            'name': campaign.name,
            'created_at': str(campaign.created_at)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_campaign_GAN.route('/campaigns/<int:campaign_id>/generate', methods=['POST'])
def generate_campaign_content(campaign_id):
    data = request.json
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Verify user owns this campaign
    if campaign.username != data['username']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get only the selected content for context
    selected_content_ids = data.get('selectedContentIds', [])
    selected_contents = CampaignContent.query\
        .filter(CampaignContent.id.in_(selected_content_ids))\
        .filter_by(campaign_id=campaign_id)\
        .order_by(CampaignContent.created_at.asc())\
        .all()
    
    # Build context only from selected contents
    context = "\n\nSelected campaign context:\n" if selected_contents else ""
    for content in selected_contents:
        context += f"- {content.description}: {content.content}\n"
    print(context)
    # Create a prompt using the provided description, parameters, and selected content
    prompt = f"""Generate campaign content for a tabletop RPG with the following parameters:
    Genre: {data.get('genre', 'science fiction')}
    Tone: {data.get('tone', 'serious')}
    Setting: {data.get('setting', 'space')}

    Here is prompt examples and format:

    Campaign &amp; Mission Creation Framework
1. Campaign Overview (High-Level Narrative Arc)
 Establish key factions (Imperial, Chaos, Xenos, Rogue Traders, etc.).
 Identify thematic influences (gritty military operations, espionage, political
intrigue, horror, large-scale warfare).
 Define the primary antagonist(s) and their motivations.
 Set up player motivations and moral dilemmas (loyalty vs. pragmatism, duty
vs. survival).
 Introduce key locations (Hive Cities, derelict Space Hulks, warzones, secret
installations).
✅ Example:
&quot;The campaign, ‘Sovereign Gambit,’ follows a crew of mercenaries under Rogue Trader
Captain Ellara Venn, as they navigate the treacherous politics of the Gilead System.
Their goal: consolidate power, strike down rivals like Jakel Varonius, and establish
dominance over key trade routes. However, the Drukhari and Chaos cults plot from the
shadows, ready to exploit any weakness.&quot;

2. Mission Framework (Modular for Each Session)
Each mission follows a structured flow that includes objectives, encounters,
complications, and rewards while maintaining narrative continuity.
Mission Name &amp; Briefing
 A concise, thematic title that fits the Warhammer 40K setting.
 Mission briefing from a key NPC (e.g., Rogue Trader, Inquisitor, Magos).
 Include stakes and context (why it matters).

✅ Example:
Mission: &quot;Ghosts of the Past&quot;
&quot;Captain Ellara Venn has received intelligence reports of a dangerous cult tied to the
Bleeding Void Kabal, led by Archon Zhaereth Vyle. Reports suggest they have
discovered a forgotten Webway route, using it to stage raids. The players must infiltrate
the suspected cult hideout, sever their connection to the Webway, and eliminate key
targets before they gain too much influence.&quot;

3. Key Mission Details
 Location &amp; Setting: Describe atmosphere, architecture, and notable details.
 Mission Goals: Primary and secondary objectives.
 Encounters &amp; Challenges: Combat, environmental hazards, roleplay
opportunities.
 Twists &amp; Complications: Unforeseen events or moral dilemmas.
 Potential Rewards: Weapons, allies, resources, intelligence.

4. Encounters &amp; Challenges (Expanded for Immersion &amp; Strategy)
Each encounter should include environmental details, tactical challenges, and
opportunities for storytelling.
Encounter Format:
✅ Name of Encounter (Combat, Investigation, Roleplay, Puzzle)
✅ Description of Location &amp; Atmosphere
✅ Enemies, NPCs, or Hazards Present
✅ Tactical Challenges &amp; Possible Player Solutions
✅ Clues or Mysteries for Story Progression

5. Example Mission Structure
Encounter 1: Approach &amp; Initial Investigation
✅ Location &amp; Atmosphere:

 The players arrive at a derelict Adeptus Mechanicus facility, its halls dark and
filled with the static hum of failing cogitators.
 The walls are slick with oil and dried blood, and there are signs of unauthorized
medical experiments.
✅ Enemies &amp; Hazards:
 Rogue servitors roam the halls, attacking anything non-Mechancium.
 Vox relay interference hints at outside forces monitoring their approach.
✅ Roleplaying &amp; Exploration:
 Logs reveal missing personnel and unauthorized medical logs signed by a now-
absent Magos.
 Players can interact with a wounded Tech-Priest, who is wary of their true
allegiance.

Encounter 2: The Unexpected Threat (Twist &amp; Complication)
✅ Location &amp; Atmosphere:
 Deep within the facility, stasis chambers line the walls, their contents obscured
by frost and bloodstained glass.
 A malfunctioning medicae servitor sits eerily still, its scalpels twitching as if
awaiting orders.
✅ Enemies &amp; Hazards:
 The Bleeding Void Kabal emerges from the shadows, having infiltrated the ship.
 Sslyth bodyguards protect a Drukhari flesh-sculptor, here to reclaim a &quot;lost
asset.&quot;
✅ Story Expansion &amp; Roleplay:
 A captured navigator pleads for help, claiming to have seen horrors beyond the
veil.
 Players may bargain, deceive, or fight their way out.

Encounter 3: The Climax &amp; Escape

✅ Location &amp; Atmosphere:
 The final chamber is an altar of surgical horror, where failed experiments
writhe in agony.
 Green luminescent runes pulse as warp energies grow unstable.
✅ Enemies &amp; Hazards:
 The Drukhari Haemonculus, Kaevos the Fleshwright, has been manipulating
events from behind the scenes.
 Escaping without retrieving key information or destroying the lab could have
dire consequences.
✅ Consequences:
 If the Navigator is lost, a powerful ally is removed from future missions.
 If the lab is left intact, it may fall into Slaaneshi cultist hands, escalating the
stakes.

6. Rewards &amp; Consequences
Every mission should provide meaningful player rewards and potential consequences
based on their actions.
✅ Examples of Potential Rewards:
 Equipment Upgrades: Enhanced weapons, xenos tech, archeotech.
 Allies &amp; Faction Influence: A navigator offers future guidance, or a Mechanicus
faction owes a favor.
 Narrative Secrets: Logs revealing hidden enemy movements or political
leverage.
✅ Examples of Consequences:
 Failure to stop a key enemy means stronger opposition later.
 Leaving an objective incomplete may trigger a future encounter or
retaliation.
 A botched diplomatic exchange leads to strained relations.

7. Overarching Narrative Progression

Each mission should feed into the larger campaign, with key events shaping the
future of the world.
 Victory in key missions should open up new opportunities (e.g., gaining
access to restricted planets, securing a powerful ally).
 Failure should lead to increased resistance, loss of trust, or an evolving
antagonist who adapts.

8. Additional Mission Hooks &amp; Future Expansion
If the GM wants to expand on current missions, include hooks for future operations,
such as:
✅ Unanswered Questions:
 What faction benefits from the players’ actions or failures?
 Is there evidence of another hidden threat (e.g., Chaos, Tyranid infestation,
political conspiracy)?
✅ Next Steps:
 Introduce a rival faction&#39;s counterattack.
 A new ally offers an opportunity that could complicate things politically.

Final Notes for Mission Creation
✅ Ensure the setting maintains Warhammer 40K’s grimdark aesthetic (brutality,
gothic horror, paranoia).
✅ Give players choices that matter, leading to future consequences.
✅ Balance action, investigation, and roleplay elements for variety.
✅ Make missions modular so they can be adjusted based on past outcomes.

    Prompt 1:
    {data.get('description')}
    {context}
    Please provide detailed and creative content that fits these parameters and maintains consistency with any provided context.


    Request: {data.get('description')}
    {context}
    Please provide detailed and creative content that fits these parameters and maintains consistency with any provided context."""

    # Generate content using the LLM
    generated_content = generate_text(prompt)
    
    if not generated_content:
        return jsonify({'error': 'Failed to generate content'}), 500
    
    # Save the generated content with all fields
    content = CampaignContent(
        campaign_id=campaign_id,
        content=generated_content,
        content_category=data.get('content_category'),
        description=data.get('description'),
        genre=data.get('genre'),
        tone=data.get('tone'),
        setting=data.get('setting')
    )
    db.session.add(content)
    db.session.commit()
    
    return jsonify({
        'id': content.id,
        'content': content.content,
        'content_category': content.content_category,
        'description': content.description,
        'genre': content.genre,
        'tone': content.tone,
        'setting': content.setting,
        'created_at': str(content.created_at)
    })

@api_campaign_GAN.route('campaigns/<int:campaign_id>/regenerate/<int:content_id>', methods=['POST'])
def regenerate_campaign_content(campaign_id, content_id):
    data = request.json
    campaign = Campaign.query.get_or_404(campaign_id)
    user_prompt = data.get('promptInput')
    
    # Verify user owns this campaign
    if campaign.username != data['username']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not user_prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    # Get original content from DB
    content = CampaignContent.query.filter_by(id=content_id, campaign_id=campaign_id).first_or_404()
    if not content:
        return jsonify({"error": "Content not found"}), 404
    
    final_prompt = (
        f"Original content:\n{content.content}\n\n"
        f"User wants to regenerate it with this instruction:\n{user_prompt}\n\n"
        f"Please regenerate the creative content that fits these instruction and maintains consistency accordingly."
    )

    # Regenerate content using the LLM
    regenerated_content = generate_text(final_prompt)

    if not regenerated_content:
        return jsonify({'error': 'Failed to regenerate content'}), 500

    # Update all fields
    content.content = regenerated_content
    content.description = content.description
    content.genre = data.get('genre', content.genre)
    content.tone = data.get('tone', content.tone)
    content.setting = data.get('setting', content.setting)

    db.session.commit()

    return jsonify({
        'id': content.id,
        'content': content.content,
        'description': content.description,
        'genre': content.genre,
        'tone': content.tone,
        'setting': content.setting,
        'created_at': str(content.created_at)
    })

@api_campaign_GAN.route('/campaigns/<int:campaign_id>/content', methods=['GET'])
def get_campaign_content(campaign_id):
    contents = CampaignContent.query.filter_by(campaign_id=campaign_id).order_by(CampaignContent.created_at.desc()).all()
    return jsonify([{
        'id': content.id,
        'content': content.content,
        'content_category': content.content_category,
        'description': content.description,
        'genre': content.genre,
        'tone': content.tone,
        'setting': content.setting,
        'created_at': str(content.created_at)
    } for content in contents])

@api_campaign_GAN.route('/campaigns/<int:campaign_id>/content', methods=['POST'])
def add_campaign_content(campaign_id):
    data = request.json
    content = CampaignContent(
        campaign_id=campaign_id,
        content_type=data['content_type'],
        content_id=data['content_id']
    )
    db.session.add(content)
    db.session.commit()
    return jsonify({'message': 'Content added successfully'})

@api_campaign_GAN.route('/campaigns/<int:campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    data = request.json
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Verify user owns this campaign
    if campaign.username != data['username']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    campaign.name = data['name']
    
    db.session.commit()
    return jsonify({
        'id': campaign.id,
        'name': campaign.name,
        'created_at': str(campaign.created_at)
    })

@api_campaign_GAN.route('/campaigns/<int:campaign_id>/content/<int:content_id>', methods=['DELETE'])
def delete_campaign_content(campaign_id, content_id):
    content = CampaignContent.query.filter_by(id=content_id, campaign_id=campaign_id).first_or_404()
    
    # Verify user owns this campaign
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
        
    if campaign.username != request.json.get('username'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(content)
    db.session.commit()
    
    return jsonify({'message': 'Content deleted successfully'})

@api_campaign_GAN.route('/campaigns/<int:campaign_id>/content/<int:content_id>', methods=['PUT'])
def update_campaign_content(campaign_id, content_id):
    data = request.json
    content = CampaignContent.query.filter_by(id=content_id, campaign_id=campaign_id).first_or_404()
    
    # Verify user owns this campaign
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
        
    if campaign.username != data.get('username'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Update all fields
    content.description = data.get('description', content.description)
    content.genre = data.get('genre', content.genre)
    content.tone = data.get('tone', content.tone)
    content.setting = data.get('setting', content.setting)
    content.content = data.get('content', content.content)
    
    db.session.commit()
    
    return jsonify({
        'id': content.id,
        'content': content.content,
        'description': content.description,
        'genre': content.genre,
        'tone': content.tone,
        'setting': content.setting,
        'created_at': str(content.created_at)
    })
