import requests
import time

url = "https://cloud.leonardo.ai/api/rest/v1/generations"

payload = {  
   "alchemy": True,  
   "height": 768,  
   "modelId": "sdxl_1_0",  
   "num_images": 4,  
   "presetStyle": "DYNAMIC",  
   "prompt": "A dnd map",  
   "width": 1024,  
   "userElements": [  
       {  
           "userLoraId": "b5c44ba2-e95c-44fa-8def-8371dfdaca71",  
           "weight": 1  
       }  
   ]  
}  
headers = {  
   "accept": "application/json",  
   "content-type": "application/json",  
   "authorization": "Bearer fab16a02-e482-4a89-a8cf-01397b4070de"  
}

try:
    # Initial generation request
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    # Get the generation ID
    generation_id = response.json().get('sdGenerationJob', {}).get('generationId')
    print(f"Generation ID: {generation_id}")
    
    if generation_id:
        # Poll for results
        max_attempts = 30
        for attempt in range(max_attempts):
            print(f"Checking attempt {attempt + 1}/{max_attempts}...")
            
            # Get the results
            results_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
            results_response = requests.get(results_url, headers=headers)
            results_response.raise_for_status()
            
            # Check if generation is complete
            generations = results_response.json().get('generations_by_pk', {})
            if generations and generations.get('status') == 'COMPLETE':
                image_urls = [gen.get('url') for gen in generations.get('generated_images', [])]
                if image_urls:
                    print("\nGenerated Image URLs:")
                    for url in image_urls:
                        print(url)
                    break
            
            time.sleep(5)  # Wait 5 seconds before next check
        
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")