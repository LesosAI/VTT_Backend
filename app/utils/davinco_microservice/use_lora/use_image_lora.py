import requests
import json
import time

def generate_map_art(api_key, description="", style="fantasy"):
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"

    # Shared style-independent prompt components
    view_prompt = (
        "Strictly top-down view, aerial perspective, bird's-eye view, "
        "orthographic projection, no tilt, no perspective distortion"
        "No text, no symbol, no watermark."
    )

    # Dynamic prompting based on style
    if style.lower() == "fantasy":
        base_prompt = f"High-resolution illustrated fantasy top-view 2D D&D battle ground map. With Description: {description}."
        style_prompt = (
            "Parchment-style with intricate related objects and elements."
            "Include varied terrain like forests, rivers, cliffs, mountains, caves, ruins, villages, and magical locations according to the description. In 2D top-down view. "
            "No grid lines, ultra-sharp details, aged look."
        )
    elif style.lower() == "sci-fi":
        base_prompt = f"High-resolution sci-fi battleground map viewed strictly from above (2D orthographic). Description: {description}."
        style_prompt = (
            "Use a top-down, futuristic holographic interface style with clean blueprint or metallic grid textures. "
            "Include only relevant elements like alien terrain, spaceports, domes, asteroid structures, lava rivers, crashed ships, and high-tech ruins, as described. "
            "No perspective distortion, no shadows suggesting depth, and absolutely no text, numbers, labels, signatures, logos, or watermarks. "
            "Map must be purely environmental, viewed directly from above with glowing accents and sharp visual contrast."
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
        "negative_prompt": "text, words, symbols, labels, signature, watermark, compass, isometric view, perspective, tilt, shadows suggesting depth, 3D objects, modern elements, logos"
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