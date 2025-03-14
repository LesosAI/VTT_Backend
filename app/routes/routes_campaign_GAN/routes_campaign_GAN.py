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
    
    # Create a prompt using the provided description and parameters
    prompt = f"""Generate campaign content for a tabletop RPG with the following parameters:
Genre: {data.get('genre', 'fantasy')}
Tone: {data.get('tone', 'serious')}
Setting: {data.get('setting', 'medieval')}

Request: {data.get('description')}

Please provide detailed and creative content that fits these parameters."""

    # Generate content using the LLM
    generated_content = generate_text(prompt)
    
    if not generated_content:
        return jsonify({'error': 'Failed to generate content'}), 500
    
    # Save the generated content with all fields
    content = CampaignContent(
        campaign_id=campaign_id,
        content=generated_content,
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
