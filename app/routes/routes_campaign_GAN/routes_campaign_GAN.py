from flask import Blueprint, request, jsonify
from app.models.user import Campaign, CampaignContent, ContentChatHistory, CharacterArt, Map, db
from datetime import datetime
from app.utils.llm_for_text import generate_text
from app.utils.tasks import background_generate_campaign, tasks
import uuid
import threading

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
        genre=data.get('genre', 'fantasy'),
        tone=data.get('tone', 'serious'),
        setting=data.get('setting', 'medieval')
    )
    
    try:
        db.session.add(campaign)
        db.session.commit()
        print(f"Campaign created: {campaign.name} by {campaign.username} having genre {campaign.genre} and tone {campaign.tone} in setting {campaign.setting}")
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
    
@api_campaign_GAN.route('/campaigns/generation-status/<string:task_id>', methods=['DELETE'])
def delete_generation_task(task_id):
    if task_id in tasks:
        del tasks[task_id]
        return jsonify({'deleted': True})
    return jsonify({'deleted': False}), 404


@api_campaign_GAN.route('/campaigns/generation-status/<string:task_id>', methods=['GET'])
def get_generation_status(task_id):
    task = tasks.get(task_id)

    if not task:
        return jsonify({'status': 'not_found'}), 404

    status = task.get('status')

    if status == 'completed':
        return jsonify({'status': 'completed', 'result': task['result'], 'should_delete': True})

    elif status == 'failed':
        return jsonify({'status': 'failed', 'error': task.get('error', 'Unknown error'), 'should_delete': True})

    return jsonify({'status': status})



@api_campaign_GAN.route('/campaigns/<int:campaign_id>/generate', methods=['POST'])
def generate_campaign_content(campaign_id):
    data = request.json
    campaign = Campaign.query.get_or_404(campaign_id)

    if campaign.username != data['username']:
        return jsonify({'error': 'Unauthorized'}), 403

    selected_content_ids = data.get('selectedContentIds', [])
    selected_contents = CampaignContent.query\
        .filter(CampaignContent.id.in_(selected_content_ids))\
        .filter_by(campaign_id=campaign_id)\
        .order_by(CampaignContent.created_at.asc())\
        .all()

    context = "\n\nSelected campaign context:\n"
    for content in selected_contents:
        context += f"- {content.description}: {content.content}\n"

    task_id = str(uuid.uuid4())
    data['campaign_id'] = campaign_id
    tasks[task_id] = {'status': 'in_progress'}

    thread = threading.Thread(target=background_generate_campaign, args=(task_id, data, context))
    thread.start()

    return jsonify({'task_id': task_id}), 202


@api_campaign_GAN.route('campaigns/<int:campaign_id>/regenerate/<int:content_id>/<string:mode>', methods=['POST'])
def regenerate_campaign_content(campaign_id, content_id, mode):
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
    
    if mode == "fully":
        # Regenerate complete content using the LLM
        final_prompt = (
            f"Original content:\n{content.content}\n\n"
            f"User wants to regenerate it with this instruction:\n{user_prompt}\n\n"
            f"Please regenerate the creative content that fits these instruction and maintains consistency accordingly."
        )

        # Regenerate content using the LLM
        regenerated_content = generate_text(final_prompt)

        if not regenerated_content:
            return jsonify({'error': 'Failed to regenerate content'}), 500

    elif mode == "partially":
        # Regenerate only the selected part of the content
        final_prompt = (
            f"Original content:\n{content.content}\n\n"
            f"The user wants to regenerate the following part:\n{data.get('selectedText')}\n\n with this instruction:\n{user_prompt}\n\n"
            f"Please regenerate only that part, keeping the rest of the story intact."
        )

        # Regenerate content using the LLM
        regenerated_content = generate_text(final_prompt)

        if not regenerated_content:
            return jsonify({'error': 'Failed to regenerate content'}), 500
        
        if data.get('selectedText') not in content.content:
            raise ValueError("Selected text not found in original content.")
        
        regenerated_content = content.content.replace(data.get('selectedText'), regenerated_content, 1)
    
    
    # Save chat history before updating
    chat_history = ContentChatHistory(
        content_id=content.id,
        content_category=content.content_category,
        message=[
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": regenerated_content}
        ],
        genre=content.genre,
        tone=content.tone,
        setting=content.setting
    )
    db.session.add(chat_history)

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

@api_campaign_GAN.route('/campaigns/<int:campaign_id>/content/<int:content_id>', methods=['GET'])
def get_content_history(campaign_id, content_id):
    
    # Get chat history for the specific content
    chat_history = ContentChatHistory.query.filter_by(content_id=content_id).order_by(ContentChatHistory.created_at.asc()).all()
    return jsonify([{
        'id': history.id,
        'content_id': history.content_id,
        'message': history.message,
        'content_category': history.content_category,
        'genre': history.genre,
        'tone': history.tone,
        'setting': history.setting,
        'created_at': str(history.created_at)
    } for history in chat_history])

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
    campaign.genre = data['genre']
    campaign.tone = data['tone']
    campaign.setting = data['setting']
    
    db.session.commit()
    return jsonify({
        'id': campaign.id,
        'name': campaign.name,
        'genre': campaign.genre,
        'tone': campaign.tone,
        'setting': campaign.setting,
        'created_at': str(campaign.created_at)
    })

@api_campaign_GAN.route('/campaigns/<int:campaign_id>/content/<int:content_id>', methods=['DELETE'])
def delete_campaign_content(campaign_id, content_id):
    content = CampaignContent.query.filter_by(id=content_id, campaign_id=campaign_id).first_or_404()
    contentHistory = ContentChatHistory.query.filter_by(content_id=content_id).all()
    
    # Verify user owns this campaign
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
        
    if campaign.username != request.json.get('username'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    for history in contentHistory:
        db.session.delete(history)

    db.session.delete(content)
    db.session.commit()
    
    return jsonify({'message': 'Content deleted successfully'})

@api_campaign_GAN.route('/campaigns/<int:campaign_id>/content/<int:content_id>/<string:action>', methods=['PUT'])
def update_campaign_content(campaign_id, content_id, action):
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

    if action == 'restore':
        previous_content = ContentChatHistory.query.filter_by(id=data.get('restoreContentId')).first_or_404()
        content.content = previous_content.message[1]['content']
    else:
        content.content = data.get('content', content.content)

    content.content_category = data.get('content_category', content.content_category)
    
    db.session.commit()

    # Save chat history before updating
    if action == 'update':
        message = [
            {"role": "user", "content": "UPDATED"},
            {"role": "assistant", "content": data.get('content')}
        ]
    elif action == 'restore':
        message = [
            {"role": "user", "content": "RESTORED"},
            {"role": "assistant", "content": content.content}
        ]
    else:
        message = [
            {"role": "user", "content": "UNKNOWN ACTION"},
            {"role": "assistant", "content": data.get('content')}
        ]

    # Create the chat history entry
    chat_history = ContentChatHistory(
        content_id=content.id,
        content_category=content.content_category,
        message=message,
        genre=content.genre,
        tone=content.tone,
        setting=content.setting
    )

    db.session.add(chat_history)
    
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
