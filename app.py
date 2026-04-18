from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests, os, sqlite3, json
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)

SUB_KEY = '78f32c698e2c466bb2405d9e7a936799'
DB = 'chats.db'

def init_db():
    con = sqlite3.connect(DB)
    con.execute('''CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        room_id TEXT,
        platform TEXT,
        customer_name TEXT,
        customer_id TEXT,
        last_message TEXT,
        last_message_time TEXT,
        last_reply_time TEXT,
        staff_name TEXT,
        status TEXT DEFAULT 'unanswered',
        created_at TEXT
    )''')
    con.commit()
    con.close()

init_db()

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
            'Ocp-Apim-Subscription-Key': '78f32c698e2c466bb2405d9e7a936799'
        },
        json=body
    )
    return jsonify(resp.json()), resp.status_code

@app.route('/webhook/venio', methods=['POST'])
def webhook():
    data = request.get_json(silent=True) or {}
    topic = data.get('Topic', '')
    event = data.get('Event', '')

    if topic == 'Chat' and event == 'Message':
        msg = data.get('Data', {}).get('ChatMessage', {})
        room_id = msg.get('RoomId', '')
        platform_num = msg.get('Platform', 0)
        platform = 'line' if platform_num == 1 else 'messenger'
        content = msg.get('Content', '')
        user = msg.get('User', {})
        customer_name = user.get('OriginalName', '')

        con = sqlite3.connect(DB)
        existing = con.execute('SELECT * FROM chats WHERE room_id=?', (room_id,)).fetchone()
        now = datetime.utcnow().isoformat()

        if existing:
            con.execute('''UPDATE chats SET
                last_message=?, last_message_time=?, status="unanswered"
                WHERE room_id=?''', (content, now, room_id))
        else:
            con.execute('''INSERT INTO chats
                (id, room_id, platform, customer_name, last_message, last_message_time, status, created_at)
                VALUES (?,?,?,?,?,?,"unanswered",?)''',
                (room_id, room_id, platform, customer_name, content, now, now))

        con.commit()
        con.close()

    return jsonify({'ok': True}), 200
    
@app.route('/api/chats', methods=['GET'])
def get_chats():
    con = sqlite3.connect(DB)
    rows = con.execute('SELECT * FROM chats ORDER BY last_message_time DESC').fetchall()
    con.close()
    cols = ['id','room_id','platform','customer_name','customer_id',
            'last_message','last_message_time','last_reply_time',
            'staff_name','status','created_at']
    return jsonify([dict(zip(cols, r)) for r in rows])

@app.route('/api/token', methods=['POST'])
def get_token():
    resp = requests.post(
        'https://api.gofive.co.th/authorization/connect/token',
        headers={'Ocp-Apim-Subscription-Key': '78f32c698e2c466bb2405d9e7a936799'},
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
