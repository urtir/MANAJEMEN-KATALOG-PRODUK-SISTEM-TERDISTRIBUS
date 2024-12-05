# client_api.py
import requests
import json
import sys

class ProductAPI:
    def __init__(self, server_ip, api_key):
        self.base_url = f'http://{server_ip}:5000'
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }

    def test_connection(self):
        """Test connection with API key authentication"""
        try:
            # Use products endpoint for testing with API key
            response = requests.get(
                f'{self.base_url}/api/products',
                headers=self.headers
            )
            if response.status_code == 401:
                print("Authentication failed - Invalid API key")
                return False
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_products(self):
        try:
            print(f"Sending request to: {self.base_url}/api/products")
            print(f"Headers: {self.headers}")
            
            response = requests.get(
                f'{self.base_url}/api/products/3',
                headers=self.headers
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 401:
                return {'error': 'Authentication failed - Invalid API key'}
            elif response.status_code == 500:
                return {'error': 'Server error - check server logs'}
            elif response.status_code != 200:
                return {'error': f'Request failed with status {response.status_code}'}
                
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': f'Connection error: {str(e)}'}
        except json.JSONDecodeError as e:
            return {'error': f'Invalid JSON response: {str(e)}'}

if __name__ == '__main__':
    SERVER_IP = 'localhost'
    API_KEY = '44c64a2dd91188892dc7a07bf7d671025be04747f9c3fcac28b1c0f7894a8321'

    api = ProductAPI(SERVER_IP, API_KEY)

    print("Testing server connection with API key...")
    if not api.test_connection():
        print(f"Cannot connect to server or authentication failed")
        sys.exit(1)

    print("\nAuthentication successful, testing API...")
    result = api.get_products()
    print(f"\nFinal Result: {result}")