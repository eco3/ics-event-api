from datetime import datetime

import requests
from flask import Blueprint, Response, jsonify, request

from app.event_fetcher import ICS_URL, fetch_events

app = Blueprint('app', __name__)

@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        events = fetch_events()
        return jsonify({"events": events})
    except Exception as e:
        return jsonify({"events": None, "error": str(e)}), 500


@app.route('/api/events', methods=['POST'])
def post_events():
    data = request.json
    current_time = data.get('current_time')

    try:
        # Check if current_time is not None and contains a 'Z' (indicating UTC time)
        #  If so, replace 'Z' with '+00:00' to make it parsable by fromisoformat
        current_time = current_time.replace("Z", "+00:00") if current_time and "Z" in current_time else current_time
        # Parse the ISO string into a datetime object if current_time is not None
        current_time = datetime.fromisoformat(current_time) if current_time else None

        events = fetch_events(current_time)
        return jsonify({"events": events})
    except ValueError:
        return jsonify({"events": None, "error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
    except Exception as e:
        return jsonify({"events": None, "error": str(e)}), 500


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