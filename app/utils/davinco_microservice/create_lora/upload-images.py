import requests
import json
import os

BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": "Bearer YOUR_API_KEY"  # Replace with your actual API key
}

def init_dataset_image_upload(dataset_id):
    """Initialise dataset image upload and get presigned URL"""
    init_url = f"{BASE_URL}/datasets/{dataset_id}/upload"
    
    payload = {"extension": "jpg"}
    
    response = requests.post(init_url, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Init dataset image upload failed: {response.text}")
    
    upload_data = response.json()['uploadDatasetImage']
    
    return {
        'url': upload_data['url'],
        'fields': json.loads(upload_data['fields']),
        'image_id': upload_data['id']
    }

def upload_image_to_s3(presigned_url, fields, image_path):
    """Upload image to S3 using presigned URL"""
    with open(image_path, 'rb') as image_file:
        files = {'file': ('image.jpg', image_file, 'image/jpg')}
        
        upload_data = fields.copy()
        
        response = requests.post(presigned_url, data=upload_data, files=files)
        
        if response.status_code not in [200, 204]:
            raise Exception(f"S3 upload failed for {image_path}: {response.text}")
    
    return True

def upload_images_to_dataset(dataset_id, image_folder):
    """Upload all images from a folder to the dataset"""
    for filename in os.listdir(image_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(image_folder, filename)
            
            # Get presigned URL
            upload_data = init_dataset_image_upload(dataset_id)
            
            # Upload to S3
            success = upload_image_to_s3(upload_data['url'], upload_data['fields'], image_path)
            
            if success:
                print(f"Successfully uploaded {filename}")
            else:
                print(f"Failed to upload {filename}")

if __name__ == "__main__":
    DATASET_ID = "YOUR_DATASET_ID"  # Replace with your dataset ID from create-dataset.py
    IMAGE_FOLDER = "images"  # Replace with your image folder path
    
    upload_images_to_dataset(DATASET_ID, IMAGE_FOLDER) 