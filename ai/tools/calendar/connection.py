
from googleapiclient.discovery import build


def get_calendar_service(credentials):
    service = build(
        "calendar",
        "v3",
        credentials=credentials,
        cache_discovery=False
    )

    return service
