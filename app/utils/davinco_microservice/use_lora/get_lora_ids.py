import requests

url = "https://cloud.leonardo.ai/api/rest/v1/elements/user/a47839cc-4ecb-4814-b557-0e384987e129"

headers = {
    "accept": "application/json",
    "authorization": "Bearer fab16a02-e482-4a89-a8cf-01397b4070de"
}

response = requests.get(url, headers=headers)

print(response.text)