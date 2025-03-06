import requests

url = "https://cloud.leonardo.ai/api/rest/v1/datasets"

payload = {
    "name": "dog-stock-photos",
    "description": "Stock photos of a small dog against pastel backgrounds"
}

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": "Bearer YOUR_API_KEY"  # Replace with your actual API key
}

response = requests.post(url, json=payload, headers=headers)

print(response.text) 