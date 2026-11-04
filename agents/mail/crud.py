from googleapiclient.discovery import build


def chat_controller(credentials):

    gmail = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    # Step 1: Inbox ke 10 email IDs fetch karo
    response = gmail.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=10
    ).execute()

    messages = response.get("messages", [])

    email_list = []

    # Step 2: Har email ki details fetch karo
    for message in messages:

        email = gmail.users().messages().get(
            userId="me",
            id=message["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()

        # Step 3: Headers extract karo
        headers = email.get("payload", {}).get("headers", [])

        email_data = {}

        for header in headers:
            name = header["name"].lower()
            email_data[name] = header["value"]

        # Step 4: Final email data
        email_list.append({
            "id": email["id"],
            "thread_id": email["threadId"],
            "sender": email_data.get("from"),
            "subject": email_data.get("subject"),
            "date": email_data.get("date"),
            "snippet": email.get("snippet")
        })

    return {
        "total": len(email_list),
        "emails": email_list
    }