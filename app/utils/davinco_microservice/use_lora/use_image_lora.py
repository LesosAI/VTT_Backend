import requests
import json
import time

def generate_map_art(api_key, description="", style="fantasy"):
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    
    # Shared style-independent prompt components
    view_prompt = "Must be a perfectly vertical top-down view, no tilt or perspective distortion."
    
    # Dynamic prompting based on style
    if style.lower() == "fantasy":
        base_prompt = f"Generate a high-resolution illustrated fantasy D&D battle map. Description: {description}."
        style_prompt = (
            "Use parchment-style with intricate hand-drawn cartographic symbols. "
            "Include varied terrain like forests, rivers, cliffs, mountains, caves, ruins, villages, and magical locations. "
            "No grid lines, no perspective, ultra-sharp details, aged look."
        )
    elif style.lower() == "sci-fi":
        base_prompt = f"Generate a sci-fi D&D top-down battle map. Description: {description}."
        style_prompt = (
            "Use futuristic cartographic symbols, top-down holographic interface style. "
            "Include alien terrain, spaceports, domes, asteroid structures, lava rivers, or crashed ships. "
            "No perspective, blueprint look or metallic grid texture, high contrast, glowing effects."
        )
    else:
        raise ValueError("Invalid style. Use 'fantasy' or 'sci-fi'.")

    # Combine all prompt parts
    full_prompt = f"{base_prompt} {style_prompt} {view_prompt}"

    payload = {
        "alchemy": True,
        "height": 768,
        "width": 1024,
        "modelId": "aa77f04e-3eec-4034-9c07-d0f619684628",
        "num_images": 4,
        "presetStyle": "DYNAMIC",
        "prompt": full_prompt,
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