import os.path
import csv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]


def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("drive", "v3", credentials=creds)

        speakers = {}
        # with open("pyladiescon-2024_speakers_confirmed.csv") as f:
        with open("sample_speaker_file.csv") as f:

            reader = csv.reader(f, delimiter=",", quotechar='"')
            for idx, row in enumerate(reader):
                print(f"{idx=}")
                print(f"{row=}")
                if idx > 0 and len(row) > 1:
                    speakers[row[0]] = {
                        "name": row[1],
                        "email": row[2],
                        "talk_title": row[3],
                    }

        for speaker_id, speaker in speakers.items():
            file_metadata = {
                "name": f"{speaker['name']} - {speaker['talk_title']}",
                "mimeType": "application/vnd.google-apps.folder",
                "parents": ["1ysaFesUhvF9i9D0aBEfL6AG8x42ldoAz"],
            }

            # create the Folder
            file = service.files().create(body=file_metadata, fields="id").execute()
            speaker["gdrive_folder_id"] = file.get("id")
            print(f"File created for {file_metadata['name']}. ID {file.get('id')}")

            # Set the permission and send email
            file_id = file.get("id")
            user_permission = {
                "type": "user",
                "role": "writer",
                "emailAddress": speaker["email"],
            }
            email_message = f"Hello {speaker['name']}, You have been granted access to the PyLadiesCon Google Drive folder for your talk titled '{speaker['talk_title']}'. Please upload your recorded talk to this folder. If you have any issues with this, please let us know. Thank you. PyLadiesCon Team"

            ids = []

            def callback(request_id, response, exception):
                if exception:
                    # Handle error
                    print(exception)
                else:
                    print(f"Request_Id: {request_id}")
                    print(f'Permission Id: {response.get("id")}')
                    ids.append(response.get("id"))

            batch = service.new_batch_http_request(callback=callback)
            batch.add(
                service.permissions().create(
                    fileId=file_id,
                    body=user_permission,
                    fields="id",
                    sendNotificationEmail=True,
                    emailMessage=email_message,
                )
            )
            batch.execute()

        with open("speaker_gdrive_folder_updated.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "speaker_id",
                    "speaker_name",
                    "speaker_email",
                    "talk_title",
                    "gdrive_folder_id",
                ]
            )
            for speaker_id, speaker in speakers.items():
                print(f"{speaker}")
                writer.writerow(
                    [
                        speaker_id,
                        speaker["name"],
                        speaker["email"],
                        speaker["talk_title"],
                        f"https://drive.google.com/drive/folders/{speaker['gdrive_folder_id']}",
                    ]
                )

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
