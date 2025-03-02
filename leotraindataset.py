import requests

url = "https://cloud.leonardo.ai/api/rest/v1/elements"

payload = {  
   "name": "dnd-map-photos",  
   "instance_prompt": "a dnd map",  
   "lora_focus": "General",  
   "train_text_encoder": True,  
   "resolution": 1024,  
   "sd_version": "SDXL_1_0",  
   "num_train_epochs": 100,  
   "learning_rate": 0.000001,  
   "description": "Dnd map",  
   "datasetId": "b5c44ba2-e95c-44fa-8def-8371dfdaca71"  
}  
headers = {  
   "accept": "application/json",  
   "content-type": "application/json",  
   "authorization": "Bearer fab16a02-e482-4a89-a8cf-01397b4070de"  
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)