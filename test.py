import requests
from flask import jsonify
from requests.auth import HTTPBasicAuth

try :
    # headers = {
    #     'Authorization': 'Basic {}'.format(
    #         base64.b64encode(
    #             '{username}:{password}'.format(
    #                 username="rayclementj",
    #                 password="Test123")
    #         )
    #     ),
    # }
    response = requests.post('https://calvinfinancialconsult.azurewebsites.net/login',auth=HTTPBasicAuth('rayclementj', 'Test123'))
    
    print (response.json())

    headers = {"Authorization": f'Bearer {response.json()["access_token"]}'}
    response = requests.get('https://calvinfinancialconsult.azurewebsites.net/api/additionalspending', headers=headers, json={'ID': '987654321'})
    print (response.json())
except Exception as e:
    print (e)