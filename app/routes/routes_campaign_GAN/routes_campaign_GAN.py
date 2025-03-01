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
        'description': c.description,
        'genre': c.genre,
        'tone': c.tone,
        'setting': c.setting,
        'created_at': str(c.created_at)
    } for c in campaigns])

@api_campaign_GAN.route('/campaigns', methods=['POST'])
def create_campaign():
    data = request.json
    campaign = Campaign(
        name=data['name'],
        username=data['username'],
        description=data.get('description'),
        genre=data.get('genre'),
        tone=data.get('tone'),
        setting=data.get('setting')
    )
    db.session.add(campaign)
    db.session.commit()
    return jsonify({
        'id': campaign.id,
        'name': campaign.name,
        'description': campaign.description
    })

@api_campaign_GAN.route('/campaigns/<int:campaign_id>/content', methods=['GET'])
def get_campaign_content(campaign_id):
    content = CampaignContent.query.filter_by(campaign_id=campaign_id).all()
    result = []
    for item in content:
        if item.content_type == 'character':
            char = CharacterArt.query.get(item.content_id)
            if char:
                result.append({
                    'type': 'character',
                    'id': char.id,
                    'image_url': char.image_url,
                    'description': char.description
                })
        elif item.content_type == 'map':
            map_item = Map.query.get(item.content_id)
            if map_item:
                result.append({
                    'type': 'map',
                    'id': map_item.id,
                    'image_url': map_item.image_url,
                    'description': map_item.description
                })
    return jsonify(result)

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
    campaign.description = data.get('description')
    campaign.genre = data.get('genre')
    campaign.tone = data.get('tone')
    campaign.setting = data.get('setting')
    
    db.session.commit()
    return jsonify({
        'id': campaign.id,
        'name': campaign.name,
        'description': campaign.description,
        'genre': campaign.genre,
        'tone': campaign.tone,
        'setting': campaign.setting
    })
