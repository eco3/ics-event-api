from datetime import datetime

from flask import Blueprint, jsonify, request

from app.event_fetcher import fetch_events

app = Blueprint('app', __name__)

@app.route('/api/events', methods=['GET'])
def get_events():
    events = fetch_events()
    return jsonify(events)

@app.route('/api/events', methods=['POST'])
def post_events():
    data = request.json
    current_time = data.get('current_time')

    if current_time:
        current_time = datetime.fromisoformat(current_time)
    else:
        current_time = None

    events = fetch_events(current_time)
    return jsonify(events)
