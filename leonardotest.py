import requests
import json
import time

def generate_character_art(api_key):
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    
    # Request payload
    payload = {
        "modelId": "6b645e3a-d64f-4341-a6d8-7a3690fbf042",  # Phoenix 0.9 model
        "prompt": "full body character portrait of a fantasy warrior, detailed character design, concept art style",
        "num_images": 1,
        "width": 1472,
        "height": 832,
        "contrast": 3.5,
        "alchemy": True,  # Quality mode
        "styleUUID": "33abbb99-03b9-4dd7-9761-ee98650b2c88",  # Cinematic Concept style
        "enhancePrompt": False
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Get the generation ID from the response
        generation_id = response.json().get('sdGenerationJob', {}).get('generationId')
        print(f"Generation ID: {generation_id}")  # Debug print
        
        # If we have a generation ID, fetch the results
        if generation_id:
            # Poll for results with timeout
            max_attempts = 30  # Maximum number of attempts
            for attempt in range(max_attempts):
                print(f"Checking attempt {attempt + 1}/{max_attempts}...")  # Debug print
                
                # Get the results
                results_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
                results_response = requests.get(results_url, headers=headers)
                results_response.raise_for_status()
                
                # Print raw response for debugging
                print(f"Response: {results_response.json()}")
                
                # Extract image URLs from the response
                generations = results_response.json().get('generations_by_pk', {})
                if generations and generations.get('status') == 'COMPLETE':
                    image_urls = [gen.get('url') for gen in generations.get('generated_images', [])]
                    if image_urls:
                        return image_urls
                
                # Wait before next attempt
                time.sleep(5)  # Check every 5 seconds
            
            print("Timed out waiting for generation to complete")
            return None
            
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

# Usage example
if __name__ == "__main__":
    api_key = "fab16a02-e482-4a89-a8cf-01397b4070de"  # Replace with your actual API key
    result = generate_character_art(api_key)
    if result:
        print("\nGenerated Image URLs:")
        for url in result:
            print(url)