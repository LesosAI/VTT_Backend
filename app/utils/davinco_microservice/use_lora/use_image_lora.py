import requests
import json
import time

def generate_map_art(api_key, description="", style="fantasy"):
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"

    # Combine prompts
    full_prompt = f"{description}. The map should include clear details of terrain, landmarks, and structures which are related. High quality, detailed cartography style. DO NOT INCLUDE GRID LINES"
    if style.lower() == "sci-fi":
        lora = 64561
    if style.lower() == "fantasy":
        lora = 64242

    payload = {
        "alchemy": True,
        "height": 768,
        "width": 1024,
        "modelId": "aa77f04e-3eec-4034-9c07-d0f619684628",
        "num_images": 1,
        "seed": 4406956102,
        "presetStyle": "DYNAMIC",
        "prompt": full_prompt,
        "userElements": [  
            {  
                "userLoraId": lora,  
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
        generation_id = response.json().get('sdGenerationJob', {}).get('generationId')

        if generation_id:
            max_attempts = 30
            for attempt in range(max_attempts):
                results_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
                results_response = requests.get(results_url, headers=headers)
                results_response.raise_for_status()
                generations = results_response.json().get('generations_by_pk', {})
                if generations and generations.get('status') == 'COMPLETE':
                    image_urls = [gen.get('url') for gen in generations.get('generated_images', [])]
                    if image_urls:
                        return image_urls[0]
                time.sleep(5)

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