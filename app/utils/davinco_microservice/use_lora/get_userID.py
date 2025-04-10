import requests

url = "https://cloud.leonardo.ai/api/rest/v1/me"

headers = {
    "accept": "application/json",
    "authorization": "Bearer d7c28aff-c4cb-45ed-b1ae-990e5be7f4ff"
}

response = requests.get(url, headers=headers)

print(response.text)