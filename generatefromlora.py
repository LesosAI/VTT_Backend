import requests
import json
import time

def generate_character_art(api_key):
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    
    # Request payload
    payload = {  
    "alchemy": True,  
    "height": 768,  
    "modelId": "aa77f04e-3eec-4034-9c07-d0f619684628",  
    "num_images": 4,  
    "presetStyle": "DYNAMIC",  
    "prompt": "A dog stock photo looking happily at the camera",  
    "width": 1024,  
    "userElements": [  
        {  
            "userLoraId": "23890",  
            "weight": 1  
        }  
    ]  
    }  
        
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}"
    }
    

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    # Get the generation ID from the response
    generation_id = response.json().get('sdGenerationJob', {}).get('generationId')
    print(f"Generation ID: {generation_id}")  # Debug print
    
      

# Usage example
if __name__ == "__main__":
    api_key = "fab16a02-e482-4a89-a8cf-01397b4070de"  # Replace with your actual API key
    result = generate_character_art(api_key)
    if result:
        print("\nGenerated Image URLs:")
        for url in result:
            print(url)