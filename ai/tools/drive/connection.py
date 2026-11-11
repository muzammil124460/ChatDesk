from googleapiclient.discovery import build


def get_drive_service(credentials):

    return build(
        "drive",
        "v3",
        credentials=credentials
    )
