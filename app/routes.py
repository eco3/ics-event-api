import requests
from datetime import datetime

from flask import Blueprint, jsonify, request, Response

from app.event_fetcher import fetch_events, ICS_URL

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

@app.route('/api/ics')
def get_ics():
    try:
        response = requests.get(ICS_URL)

        if response.status_code == 200:
            return Response(
                response=response.content,
                mimetype="text/calendar",
                headers={"Content-Disposition": f"attachment; filename=cto-calendar.ics"}
            )
        else:
            return f"Failed to fetch ICS file. Status code {response.status_code}", 500
    except requests.exceptions.RequestException as e:
        return f"An error occured: {str(e)}", 500