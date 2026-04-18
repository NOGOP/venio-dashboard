from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests, os

app = Flask(__name__, static_folder='static')
CORS(app)

SUB_KEY = '78f32c698e2c466bb2405d9e7a936799'

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/conversations', methods=['POST'])
def conversations():
    token = request.headers.get('Authorization', '')
    body = request.get_json()
    resp = requests.post(
        'https://api.gofive.co.th/v1/conversation/enquiry',
        headers={
            'Content-Type': 'application/json',
            'Authorization': token,
            'Ocp-Apim-Subscription-Key': SUB_KEY
        },
        json=body
    )
    return jsonify(resp.json()), resp.status_code

@app.route('/api/token', methods=['POST'])
def get_token():
    resp = requests.post(
        'https://api.gofive.co.th/authorization/connect/token',
        headers={'Ocp-Apim-Subscription-Key': SUB_KEY},
        data={
            'grant_type': 'client_credentials',
            'client_id': os.environ.get('CLIENT_ID', ''),
            'client_secret': os.environ.get('CLIENT_SECRET', '')
        }
    )
    return jsonify(resp.json()), resp.status_code

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
