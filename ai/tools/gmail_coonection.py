from googleapiclient.discovery import build



def get_gmail_service(credentials):
    return build(
        "gmail",
        "v1",
        credentials=credentials
    )