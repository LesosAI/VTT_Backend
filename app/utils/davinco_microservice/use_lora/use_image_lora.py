import requests
import json
import time

def generate_map_art(api_key, description=""):
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    
    # Construct the prompt using the provided description
    base_prompt = f"Generate a top-down view D&D map based on this description: {description}. "
    style_prompt = "The map should include clear details of terrain, landmarks, and structures. High quality, detailed cartography style. DO NOT INCLUDE GRID LINES"
    view_prompt = "Must be a perfect top-down view looking directly down at the map"
    
    # Combine prompts
    full_prompt = f"{base_prompt} {style_prompt} {view_prompt}"
    
    # Request payload
    payload = {  
        "alchemy": True,  
        "height": 768,  
        "modelId": "aa77f04e-3eec-4034-9c07-d0f619684628",  
        "num_images": 4,  
        "presetStyle": "DYNAMIC",  
        "prompt": full_prompt,  
        "width": 1024,  
        "userElements": [  
            {  
                "userLoraId": 23890,  
                "weight": 1  
            }  
        ]  
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
                print(f"Checking attempt {attempt + 1}/{max_attempts}...")
                
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
                        return image_urls[0]  # Return the first generated image URL
                
                # Wait before next attempt
                time.sleep(5)  # Check every 5 seconds
            
            print("Timed out waiting for generation to complete")
            return None
            
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

# Usage example
if __name__ == "__main__":
    api_key = "d7c28aff-c4cb-45ed-b1ae-990e5be7f4ff"  # Replace with your actual API key
    result = generate_map_art(api_key)
    if result:
        print("\nGenerated Image URL:")
        print(result)