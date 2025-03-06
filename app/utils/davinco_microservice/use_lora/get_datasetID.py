import requests

url = "https://cloud.leonardo.ai/api/rest/v1/datasets"

payload = {  
   "name": "dnd-map-photos",  
   "description": "Stock photos of a dnd map"  
}  
headers = {  
   "accept": "application/json",  
   "content-type": "application/json",  
   "authorization": "Bearer fab16a02-e482-4a89-a8cf-01397b4070de"  
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)