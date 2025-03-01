from flask import Blueprint, request, jsonify, send_file, make_response
from app.models.user import CharacterArt, User, db, Tag
import requests
from datetime import datetime
from PIL import Image, ImageDraw
import io

api_campaign_GAN = Blueprint("api_campaign_GAN", __name__, url_prefix="/api")

@api_campaign_GAN.route('/generate-campaign', methods=['POST'])
def generate_campaign():
    data = request.json
