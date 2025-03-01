from flask import Blueprint, request, jsonify
from app.models.user import Campaign, CampaignContent, CharacterArt, Map, db
from datetime import datetime

api_campaign_GAN = Blueprint("api_campaign_GAN", __name__, url_prefix="/api")

@api_campaign_GAN.route('/campaigns/<username>', methods=['GET'])
def get_campaigns(username):
    campaigns = Campaign.query.filter_by(username=username).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'genre': c.genre,
        'tone': c.tone,
        'setting': c.setting,
        'created_at': str(c.created_at)
    } for c in campaigns])

@api_campaign_GAN.route('/campaigns', methods=['POST'])
def create_campaign():
    data = request.json
    if not data.get('name') or not data.get('username'):
        return jsonify({'error': 'Name and username are required'}), 400
        
    campaign = Campaign(
        name=data['name'],
        username=data['username'],
        genre=data.get('genre'),
        tone=data.get('tone'),
        setting=data.get('setting')
    )
    
    try:
        db.session.add(campaign)
        db.session.commit()
        return jsonify({
            'id': campaign.id,
            'name': campaign.name,
            'genre': campaign.genre,
            'tone': campaign.tone,
            'setting': campaign.setting,
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
    
    # Here you would call your text generation service
    # For now, let's just create a placeholder
    generated_text = f"Generated content for {campaign.name} in {campaign.genre} style..."
    
    # Save the generated content with description
    content = CampaignContent(
        campaign_id=campaign_id,
        content=generated_text,
        description=data.get('description')  # Optional description from user
    )
    db.session.add(content)
    db.session.commit()
    
    return jsonify({
        'id': content.id,
        'content': content.content,
        'description': content.description,
        'created_at': str(content.created_at)
    })

@api_campaign_GAN.route('/campaigns/<int:campaign_id>/content', methods=['GET'])
def get_campaign_content(campaign_id):
    contents = CampaignContent.query.filter_by(campaign_id=campaign_id).order_by(CampaignContent.created_at.desc()).all()
    return jsonify([{
        'id': content.id,
        'content': content.content,
        'description': content.description,
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
    campaign.genre = data.get('genre')
    campaign.tone = data.get('tone')
    campaign.setting = data.get('setting')
    
    db.session.commit()
    return jsonify({
        'id': campaign.id,
        'name': campaign.name,
        'genre': campaign.genre,
        'tone': campaign.tone,
        'setting': campaign.setting
    })

@api_campaign_GAN.route('/campaigns/<int:campaign_id>/content/<int:content_id>', methods=['PUT'])
def update_campaign_content(campaign_id, content_id):
    data = request.json
    content = CampaignContent.query.filter_by(id=content_id, campaign_id=campaign_id).first_or_404()
    
    # Update description
    content.description = data.get('description')
    db.session.commit()
    
    return jsonify({
        'id': content.id,
        'content': content.content,
        'description': content.description,
        'created_at': str(content.created_at)
    })
