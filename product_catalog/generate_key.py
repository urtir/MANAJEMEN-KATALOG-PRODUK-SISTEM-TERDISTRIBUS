# generate_key.py
import requests
import json

response = requests.post(
    'http://localhost:5000/api/keys',
    json={'client_name': 'device23'}
)
print(response.json())