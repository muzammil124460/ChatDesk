
import json
from datetime import datetime, timezone
from typing import Optional

from langchain_core.tools import tool
from ai.tools.calendar.connection import get_calendar_service


def get_calendar_tools(credentials):

    service = get_calendar_service(credentials)

    @tool
    def list_events(max_results: int = 10):
        """
        List upcoming events from the user's primary Google Calendar.
        Use this when the user asks about upcoming meetings or events.
        """

        try:
            now = datetime.now(timezone.utc).isoformat()

            response = service.events().list(
                calendarId="primary",
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = response.get("items", [])

            result = []

            for event in events:
                result.append({
                    "id": event.get("id"),
                    "summary": event.get("summary"),
                    "description": event.get("description"),
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "location": event.get("location"),
                    "htmlLink": event.get("htmlLink")
                })

            return json.dumps(result, indent=2)

        except Exception as e:
            return f"Error listing events: {str(e)}"

    @tool
    def search_events(query: str, max_results: int = 10):
        """
        Search calendar events using a keyword.
        Example: search_events("interview")
        """

        try:
            response = service.events().list(
                calendarId="primary",
                q=query,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = response.get("items", [])

            result = []

            for event in events:
                result.append({
                    "id": event.get("id"),
                    "summary": event.get("summary"),
                    "description": event.get("description"),
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "location": event.get("location"),
                    "htmlLink": event.get("htmlLink")
                })

            return json.dumps(result, indent=2)

        except Exception as e:
            return f"Error searching events: {str(e)}"

    @tool
    def create_event(
        summary: str,
        start_datetime: str,
        end_datetime: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone_name: str = "Asia/Kolkata"
    ):
        """
        Create a calendar event.

        start_datetime and end_datetime must use ISO format:
        YYYY-MM-DDTHH:MM:SS

        Example:
        2026-11-15T10:00:00

        Use the user's requested date and time. Do not invent them.
        """

        try:
            event_body = {
                "summary": summary,
                "start": {
                    "dateTime": start_datetime,
                    "timeZone": timezone_name
                },
                "end": {
                    "dateTime": end_datetime,
                    "timeZone": timezone_name
                }
            }

            if description:
                event_body["description"] = description

            if location:
                event_body["location"] = location

            event = service.events().insert(
                calendarId="primary",
                body=event_body
            ).execute()

            return json.dumps({
                "message": "Event created successfully",
                "id": event.get("id"),
                "summary": event.get("summary"),
                "htmlLink": event.get("htmlLink")
            }, indent=2)

        except Exception as e:
            return f"Error creating event: {str(e)}"

    @tool
    def update_event(
        event_id: str,
        summary: Optional[str] = None,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone_name: str = "Asia/Kolkata"
    ):
        """
        Update an existing calendar event.
        First search for the event and obtain its exact event_id.
        Only supplied fields will be updated.
        """

        try:
            event_body = {}

            if summary is not None:
                event_body["summary"] = summary

            if description is not None:
                event_body["description"] = description

            if location is not None:
                event_body["location"] = location

            if start_datetime is not None:
                event_body["start"] = {
                    "dateTime": start_datetime,
                    "timeZone": timezone_name
                }

            if end_datetime is not None:
                event_body["end"] = {
                    "dateTime": end_datetime,
                    "timeZone": timezone_name
                }

            if not event_body:
                return "No update fields provided."

            event = service.events().patch(
                calendarId="primary",
                eventId=event_id,
                body=event_body
            ).execute()

            return json.dumps({
                "message": "Event updated successfully",
                "id": event.get("id"),
                "summary": event.get("summary"),
                "htmlLink": event.get("htmlLink")
            }, indent=2)

        except Exception as e:
            return f"Error updating event: {str(e)}"

    @tool
    def delete_event(event_id: str):
        """
        Delete an event from the user's primary calendar.
        Only call this when the user explicitly asks to delete
        the identified event. Obtain confirmation through the
        application's approval flow before executing deletion.
        """

        try:
            service.events().delete(
                calendarId="primary",
                eventId=event_id
            ).execute()

            return "Event deleted successfully."

        except Exception as e:
            return f"Error deleting event: {str(e)}"

    return [
        list_events,
        search_events,
        create_event,
        update_event,
        delete_event
    ]
