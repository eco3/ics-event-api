import logging
from datetime import datetime

import requests
from flask import Blueprint, Response, jsonify, request

from app.event import EventList
from app.event_fetcher import fetch_events, fetch_ics

app = Blueprint('app', __name__)
logger = logging.getLogger(__name__)

INVALID_DATE_ERROR = "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"


def _error(message: str, status: int):
    return jsonify({"events": None, "error": message}), status


def _events_response(current_time=None):
    # Exception details stay in the server log: upstream errors include the
    # full ICS_URL, which for a private feed contains a secret token.
    try:
        event_list: EventList = fetch_events(current_time)
    except requests.RequestException:
        logger.exception("Failed to fetch the ICS calendar")
        return _error("Failed to fetch the calendar", 502)
    except Exception:
        logger.exception("Failed to process the ICS calendar")
        return _error("Internal server error", 500)

    return jsonify({"events": event_list.serialize()})


@app.route('/api/events', methods=['GET'])
def get_events():
    return _events_response()


@app.route('/api/events', methods=['POST'])
def post_events():
    data = request.get_json(silent=True)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return _error("Request body must be a JSON object", 400)

    current_time = data.get('current_time')
    if current_time is not None and not isinstance(current_time, str):
        return _error(INVALID_DATE_ERROR, 400)

    if current_time:
        try:
            # fromisoformat on Python 3.11+ accepts a trailing 'Z' (UTC)
            current_time = datetime.fromisoformat(current_time)
        except ValueError:
            return _error(INVALID_DATE_ERROR, 400)
    else:
        current_time = None

    return _events_response(current_time)


@app.route('/api/ics')
def get_ics():
    try:
        content = fetch_ics()
    except requests.RequestException:
        logger.exception("Failed to fetch the ICS calendar")
        return _error("Failed to fetch the calendar", 502)

    return Response(
        response=content,
        mimetype="text/calendar",
        headers={"Content-Disposition": "attachment; filename=calendar.ics"}
    )
