
import json
import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from langchain.tools import tool

from ai.tools.drive.connection import get_drive_service
import os
import tempfile
from markitdown import MarkItDown

def get_drive_tools(credentials):

    service = get_drive_service(credentials)


    @tool
    def list_files( page_size: int = 10):

        """List files and folders from Google Drive."""


        response = service.files().list(
            pageSize=page_size,
            fields="files(id,name,mimeType,webViewLink,modifiedTime)"
        ).execute()

        return json.dumps(response.get("files", []), indent=2)


    @tool
    def search_files(query: str):
        """Search Google Drive files using a Google Drive API query."""

        response = service.files().list(
            q=f"({query}) and trashed = false",
            fields="files(id,name,mimeType,webViewLink)"
        ).execute()

        return json.dumps(response.get("files", []), indent=2)


    @tool
    def upload_file( file_path: str):

        """Upload a local file to Google Drive."""


        media = MediaIoBaseUpload(
            io.FileIO(file_path, "rb"),
            mimetype="application/octet-stream",
            resumable=True
        )

        response = service.files().create(
            body={"name": file_path.split("/")[-1].split("\\")[-1]},
            media_body=media,
            fields="id,name,webViewLink"
        ).execute()

        return json.dumps(response, indent=2)


    @tool
    def download_file( file_id: str):

        """Download a Google Drive file by its ID."""


        request = service.files().get_media(fileId=file_id)

        file_data = io.BytesIO()

        downloader = MediaIoBaseDownload(file_data, request)

        done = False

        while not done:
            status, done = downloader.next_chunk()

        return {
            "file_id": file_id,
            "content": file_data.getvalue().hex()
        }


    
    @tool
    def read_file(file_id: str):
        """Read supported document formats from Google Drive."""

        file_info = service.files().get(
            fileId=file_id,
            fields="id,name,mimeType"
        ).execute()

        name = file_info["name"]
        mime_type = file_info["mimeType"]

        # Google Workspace native files
        export_types = {
            "application/vnd.google-apps.document": (
                "text/plain", ".txt"
            ),
            "application/vnd.google-apps.spreadsheet": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".xlsx"
            ),
            "application/vnd.google-apps.presentation": (
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                ".pptx"
            )
        }

        temp_path = None

        try:
            if mime_type in export_types:
                export_mime, suffix = export_types[mime_type]

                file_bytes = service.files().export(
                    fileId=file_id,
                    mimeType=export_mime
                ).execute()

            else:
                suffix = os.path.splitext(name)[1]

                file_bytes = service.files().get_media(
                    fileId=file_id
                ).execute()

            # Save temporarily
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix
            ) as temp:
                temp.write(file_bytes)
                temp_path = temp.name

            # Convert document into Markdown
            converter = MarkItDown()
            result = converter.convert(temp_path)

            return result.markdown

        except Exception as e:
            return f"Unable to read {name}: {str(e)}"

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)



    return [
            list_files,
            search_files,
            upload_file,
            download_file,
            read_file
        ]
