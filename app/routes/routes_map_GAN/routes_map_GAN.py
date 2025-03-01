from flask import Blueprint, request, jsonify, send_file, make_response
from app.models.user import CharacterArt, User, db, Tag
import requests
from datetime import datetime
from PIL import Image, ImageDraw
import io

api_map_GAN = Blueprint("api_map_GAN", __name__, url_prefix="/api")

@api_map_GAN.route('/generate-map', methods=['POST'])
def generate_map():
    data = request.json
