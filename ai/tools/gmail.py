




    
import base64
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from langchain_core.tools import tool


def create_gmail_tools(credentials):

    # =====================================
    # 1. Create Gmail service only once
    # =====================================

    service = build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False
    )

    # =====================================
    # Helper functions
    # =====================================

    def decode_data(data):
        if not data:
            return ""

        # Gmail uses URL-safe Base64
        data += "=" * (-len(data) % 4)

        decoded = base64.urlsafe_b64decode(data)

        return decoded.decode("utf-8", errors="replace")


    def get_header(headers, name):
        for header in headers:
            if header.get("name", "").lower() == name.lower():
                return header.get("value", "")

        return ""


    def get_parts(payload):
        parts = []

        if payload.get("parts"):
            for part in payload["parts"]:
                parts.extend(get_parts(part))
        else:
            parts.append(payload)

        return parts


    def extract_body(payload):
        parts = get_parts(payload)

        # Prefer plain text
        for part in parts:
            mime_type = part.get("mimeType", "")

            if mime_type == "text/plain":
                data = part.get("body", {}).get("data")

                if data:
                    return decode_data(data)

        # Fallback to HTML
        for part in parts:
            mime_type = part.get("mimeType", "")

            if mime_type == "text/html":
                data = part.get("body", {}).get("data")

                if data:
                    return decode_data(data)

        return ""


    def extract_email_details(message):

        payload = message.get("payload", {})
        headers = payload.get("headers", [])

        return {
            "id": message.get("id"),
            "thread_id": message.get("threadId"),
            "sender": get_header(headers, "From"),
            "to": get_header(headers, "To"),
            "subject": get_header(headers, "Subject"),
            "date": get_header(headers, "Date"),
            "snippet": message.get("snippet", ""),
            "body": extract_body(payload)
        }


    def create_raw_message(to, subject, body, cc="", bcc=""):

        email_message = MIMEText(body, "plain", "utf-8")

        email_message["To"] = to
        email_message["Subject"] = subject

        if cc:
            email_message["Cc"] = cc

        if bcc:
            email_message["Bcc"] = bcc

        raw = base64.urlsafe_b64encode(
            email_message.as_bytes()
        ).decode("utf-8")

        return raw


    # =====================================
    # A. READING TOOLS
    # =====================================

    # 1. Search emails

    @tool
    def search_emails(query: str):
        """
        Search Gmail using queries like:
        from:google, is:unread, subject:meeting.
        """

        result = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=10
        ).execute()

        return {
            "emails": result.get("messages", []),
            "next_page_token": result.get("nextPageToken")
        }


    # 2. List recent emails

    @tool
    def list_emails(max_results: int = 10):
        """
        Get recent emails from the inbox.
        """

        max_results = max(1, min(max_results, 100))

        result = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=max_results
        ).execute()

        return result.get("messages", [])


    # 3. Read email

    @tool
    def read_email(email_id: str):
        """
        Read an email using its Gmail message ID.
        """

        message = service.users().messages().get(
            userId="me",
            id=email_id,
            format="full"
        ).execute()

        return extract_email_details(message)


    # 4. Get complete email conversation

    @tool
    def get_email_thread(thread_id: str):
        """
        Get all messages from an email conversation.
        """

        thread = service.users().threads().get(
            userId="me",
            id=thread_id,
            format="full"
        ).execute()

        messages = []

        for message in thread.get("messages", []):
            messages.append(
                extract_email_details(message)
            )

        return messages


    # 5. Get email attachments

    @tool
    def get_attachments(email_id: str):
        """
        Get attachment names, types and Base64 content.
        Attachments larger than 5 MB are skipped.
        """

        message = service.users().messages().get(
            userId="me",
            id=email_id,
            format="full"
        ).execute()

        payload = message.get("payload", {})
        attachments = []

        for part in get_parts(payload):

            filename = part.get("filename")

            if not filename:
                continue

            body = part.get("body", {})
            size = body.get("size", 0)
            attachment_id = body.get("attachmentId")

            if not attachment_id:
                continue

            if size > 5 * 1024 * 1024:
                attachments.append({
                    "filename": filename,
                    "status": "skipped",
                    "reason": "Attachment is larger than 5 MB"
                })
                continue

            attachment = service.users().messages().attachments().get(
                userId="me",
                messageId=email_id,
                id=attachment_id
            ).execute()

            content = decode_data(
                attachment.get("data", "")
            )

            # Return Base64 so the application can save the file.
            original_data = base64.urlsafe_b64decode(
                attachment["data"] + "=" * (-len(attachment["data"]) % 4)
            )

            attachments.append({
                "filename": filename,
                "mime_type": part.get("mimeType"),
                "size": size,
                "content_base64": base64.b64encode(
                    original_data
                ).decode("utf-8")
            })

        return attachments


    # =====================================
    # B. EMAIL MANAGEMENT TOOLS
    # =====================================

    # 6. Mark email as read

    @tool
    def mark_as_read(email_id: str):
        """
        Mark an email as read.
        """

        result = service.users().messages().modify(
            userId="me",
            id=email_id,
            body={
                "removeLabelIds": ["UNREAD"]
            }
        ).execute()

        return {"status": "marked_as_read", "id": result.get("id")}


    # 7. Mark email as unread

    @tool
    def mark_as_unread(email_id: str):
        """
        Mark an email as unread.
        """

        result = service.users().messages().modify(
            userId="me",
            id=email_id,
            body={
                "addLabelIds": ["UNREAD"]
            }
        ).execute()

        return {"status": "marked_as_unread", "id": result.get("id")}


    # 8. Archive email

    @tool
    def archive_email(email_id: str):
        """
        Remove an email from the inbox without deleting it.
        """

        result = service.users().messages().modify(
            userId="me",
            id=email_id,
            body={
                "removeLabelIds": ["INBOX"]
            }
        ).execute()

        return {"status": "archived", "id": result.get("id")}


    # 9. Move email to trash

    @tool
    def trash_email(email_id: str):
        """
        Move an email to Gmail trash.
        """

        result = service.users().messages().trash(
            userId="me",
            id=email_id
        ).execute()

        return {"status": "moved_to_trash", "id": result.get("id")}


    # 10. Manage labels

    @tool
    def manage_labels(
        action: str,
        email_id: str = "",
        label_id: str = "",
        label_name: str = ""
    ):
        """
        Manage Gmail labels.

        Actions:
        list, create, apply, remove.
        """

        if action == "list":

            result = service.users().labels().list(
                userId="me"
            ).execute()

            return result.get("labels", [])


        elif action == "create":

            if not label_name:
                return {"error": "label_name is required"}

            result = service.users().labels().create(
                userId="me",
                body={"name": label_name}
            ).execute()

            return result


        elif action == "apply":

            if not email_id or not label_id:
                return {"error": "email_id and label_id are required"}

            result = service.users().messages().modify(
                userId="me",
                id=email_id,
                body={
                    "addLabelIds": [label_id]
                }
            ).execute()

            return {"status": "label_applied", "id": result.get("id")}


        elif action == "remove":

            if not email_id or not label_id:
                return {"error": "email_id and label_id are required"}

            result = service.users().messages().modify(
                userId="me",
                id=email_id,
                body={
                    "removeLabelIds": [label_id]
                }
            ).execute()

            return {"status": "label_removed", "id": result.get("id")}


        return {
            "error": "Invalid action. Use list, create, apply or remove."
        }


    # =====================================
    # C. EMAIL COMMUNICATION TOOLS
    # =====================================

    # 11. Send new email

    @tool
    def send_email(
        to: str,
        subject: str,
        body: str,
        cc: str = "",
        bcc: str = ""
    ):
        """
        Send a new email.
        """

        raw = create_raw_message(
            to, subject, body, cc, bcc
        )

        result = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        return {
            "status": "sent",
            "message_id": result.get("id"),
            "thread_id": result.get("threadId")
        }


    # 12. Reply to email

    @tool
    def reply_email(email_id: str, body: str):
        """
        Reply to an existing email.
        """

        original = service.users().messages().get(
            userId="me",
            id=email_id,
            format="full"
        ).execute()

        payload = original.get("payload", {})
        headers = payload.get("headers", [])

        recipient = (
            get_header(headers, "Reply-To")
            or get_header(headers, "From")
        )

        subject = get_header(headers, "Subject")
        message_id = get_header(headers, "Message-ID")
        references = get_header(headers, "References")

        if not recipient or not message_id:
            return {"error": "Original reply information is missing"}

        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        reply = MIMEText(body, "plain", "utf-8")
        reply["To"] = recipient
        reply["Subject"] = subject
        reply["In-Reply-To"] = message_id
        reply["References"] = f"{references} {message_id}".strip()

        raw = base64.urlsafe_b64encode(
            reply.as_bytes()
        ).decode("utf-8")

        result = service.users().messages().send(
            userId="me",
            body={
                "raw": raw,
                "threadId": original.get("threadId")
            }
        ).execute()

        return {
            "status": "reply_sent",
            "message_id": result.get("id"),
            "thread_id": result.get("threadId")
        }


    # 13. Forward email

    @tool
    def forward_email(email_id: str, to: str):
        """
        Forward an email as quoted text.
        Original attachments are not forwarded by this version.
        """

        original = service.users().messages().get(
            userId="me",
            id=email_id,
            format="full"
        ).execute()

        details = extract_email_details(original)

        forwarded_body = f"""
---------- Forwarded message ----------

From: {details["sender"]}
Date: {details["date"]}
Subject: {details["subject"]}

{details["body"]}
"""

        subject = details["subject"]

        if not subject.lower().startswith("fwd:"):
            subject = f"Fwd: {subject}"

        raw = create_raw_message(
            to,
            subject,
            forwarded_body
        )

        result = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        return {
            "status": "forwarded",
            "message_id": result.get("id")
        }


    # 14. Create draft

    @tool
    def create_draft(
        to: str,
        subject: str,
        body: str
    ):
        """
        Create an email draft without sending it.
        """

        raw = create_raw_message(
            to, subject, body
        )

        result = service.users().drafts().create(
            userId="me",
            body={
                "message": {
                    "raw": raw
                }
            }
        ).execute()

        return {
            "status": "draft_created",
            "draft_id": result.get("id")
        }


    # 15. Send saved draft

    @tool
    def send_draft(draft_id: str):
        """
        Send an existing Gmail draft.
        """

        result = service.users().drafts().send(
            userId="me",
            body={
                "id": draft_id
            }
        ).execute()

        return {
            "status": "draft_sent",
            "message_id": result.get("id"),
            "thread_id": result.get("threadId")
        }


    # =====================================
    # Return all 15 tools
    # =====================================

    return [
        search_emails,
        list_emails,
        read_email,
        get_email_thread,
        get_attachments,
        mark_as_read,
        mark_as_unread,
        archive_email,
        trash_email,
        manage_labels,
        send_email,
        reply_email,
        forward_email,
        create_draft,
        send_draft
    ]

