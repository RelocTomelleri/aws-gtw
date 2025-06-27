import sys
import os
import requests

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(BASE_DIR, 'config'))

from client_cloud.config.aws_config import aws

def call_api_get(url, id_token=None):
    headers = {
        'Content-Type': 'application/json'
    }
    if id_token:  # aggiungi header solo se fornito
        headers['Authorization'] = id_token

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')

        if 'application/json' in content_type:
            return response.json()
        else:
            # Ritorna un dizionario con metadata e contenuto raw
            return {
                "headers": dict(response.headers),
                "content_type": content_type,
                "content": response.content
            }
    except requests.exceptions.RequestException as e:
        print(f"Errore durante la chiamata GET: {e}")
        return None

def call_api_post(url, id_token, payload):
    headers = {
        'Authorization': id_token,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Errore durante la chiamata POST: {e}")
        return None

def call_api_del(url, id_token):
    headers = {
        'Authorization': id_token,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()

        # Verifica se la risposta è JSON
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            return response.json()
        else:
            return {
                "content_type": content_type,
                "content": response.content
            }

    except requests.exceptions.RequestException as e:
        print(f"Errore durante la chiamata DELETE: {e}")
        return None


# Funzioni specifiche per le tue API AWS

def get_gateway_info(id_token, gateway_id):
    url = f"{aws['api_endpoint']}/gateways/{gateway_id}"
    return call_api_get(url, id_token)

### FE:
# Add gateway
def provision_gateway(id_token, payload):
    url = f"{aws['api_endpoint']}/api/v0/gateways"
    return call_api_post(url, id_token, payload)

# Add gateway
def delete_gateway(id_token, gateway_id):
    url = f"{aws['api_endpoint']}/api/v0/gateways/{gateway_id}"
    return call_api_del(url, id_token)

# GTW: api
def get_credentials(passwordRoot, gateway_id):
    url = f"{aws['api_endpoint']}/api/v0/credentials/{gateway_id}"
    print(f"Url: \t{url}\nPasswordRoot: \t{passwordRoot}")
    return call_api_get(url, passwordRoot)

def get_config_bin(configId):
    url = f"{aws['api_endpoint']}/api/v0/configurations/{configId}/bin"
    print(f"Url: \t{url}\nConfigId: \t{configId}")
    return call_api_get(url)
