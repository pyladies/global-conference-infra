import httpx
import os
import os.path
import csv
import io
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

import subprocess

from enum import StrEnum

BASE_URL = "https://pretalx.com/api/events/pyladiescon-2024/"
SCOPES = ["https://www.googleapis.com/auth/drive",
          "https://www.googleapis.com/auth/spreadsheets"
          ]
GSHEET_ID = os.getenv("GSHEET_ID")
SHEET_TAB = "schedule_autogen"
PRETALX_API_TOKEN = os.getenv("PRETALX_API_TOKEN")

MAIN_STREAM_ROOM = "Main Stream"
MAX_SECONDS = 1200 # 20 minutes

class SubmissionType(StrEnum):
    TALK = "talk"
    WORKSHOP = "workshop"
    KEYNOTE = "keynote"
    PANEL = "panel"
    SPRINT = "sprint"

class SubmissionState(StrEnum):
    CONFIRMED = "confirmed"

class Session:
    def __init__(self, session_dict):
        self.session_code = session_dict["code"]
        self.title = session_dict["title"]
        if not session_dict["submission_type"].get("es"):
            submission_type = session_dict["submission_type"]["en"]
        else:
            submission_type = session_dict["submission_type"]["es"]
        self.submission_type = None
        if submission_type == "Talk":
            self.submission_type = SubmissionType.TALK.value
        elif submission_type in ["Workshop", "Taller (60 minutos)", "Taller (90 minutos)"]:
            self.submission_type = SubmissionType.WORKSHOP.value
        elif submission_type == "Panel":
            self.submission_type = SubmissionType.PANEL.value
        elif submission_type == "Keynote":
            self.submission_type = SubmissionType.KEYNOTE.value
        elif submission_type == "Sprints guiados":
            self.submission_type = SubmissionType.SPRINT.value
        else:
            print("Unknown session type", submission_type)
        if session_dict["state"] == "confirmed":
            self.state = SubmissionState.CONFIRMED.value
        else:
            print("Unknown state", session_dict["state"])
        self.state = session_dict["state"]
        if session_dict.get("slot"):
            self.start_time = datetime.fromisoformat(session_dict["slot"]["start"])
            self.end_time = datetime.fromisoformat(session_dict["slot"]["end"])
            self.room = session_dict["slot"]["room"]["en"]
        else:
            self.start_time = None
            self.end_time = None
            self.room = None
        self.speakers = []
        for speaker in session_dict["speakers"]:
            self.add_speaker(speaker)
        self.gdrive_id = ""
        self.video_received = False
        self.video_length = 0
        self.video_duration = ''
        self.video_within_limit = None
        self.q_a = ''


    def add_speaker(self, speaker_dict):
        speaker = Speaker(speaker_dict)
        self.speakers.append(speaker)

        # self.submission_type
    def print_speakers(self):
        if len(self.speakers) > 1:
            return ",".join([speaker.name for speaker in self.speakers])
        else:
            return self.speakers[0].name
    def to_dict(self):
        return {
            "session_code": self.session_code,
            "title": self.title,
            "submission_type": self.submission_type,
            "state": self.state,
            "room": self.room,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "speakers": self.print_speakers(),
            "gdrive_id": self.gdrive_id,
            "video_received": self.video_received,
            "video_length": self.video_length,
            "video_duration": str(self.video_duration),
            "video_within_limit": self.video_within_limit,
            "q_a": self.q_a,
            "gdrive_url": f"https://drive.google.com/drive/folders/{self.gdrive_id}" if self.gdrive_id else ""
        }

class Speaker:
    def __init__(self, speaker_dict):
        self.speaker_id = speaker_dict["code"]
        self.name = speaker_dict["name"]
        self.email = speaker_dict["email"]

    def to_dict(self):
        return {
            "speaker_id": self.speaker_id,
            "name": self.name,
            "email": self.email
        }


class PretalxWrapper:
    def __init__(self, token):
        self.headers = {"Authorization": f"Token {token}"}

    def get_submissions(self):
        params = {"state": "confirmed"}
        has_response = True
        url = BASE_URL + "submissions/"
        index = 0
        while has_response:
            response = httpx.get(url, headers=self.headers, params=params)
            url = response.json()["next"]
            has_response = url is not None
            for r in response.json()["results"]:
                index += 1
                yield r

def get_audio_length(filepath):
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
             filepath], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return float(result.stdout)
    except Exception as e:
        print(f"Error getting audio length for file {filepath}", e)
    return 0


class PyLadiesCon:
    def __init__(self):
        self.pretalx_wrapper = PretalxWrapper(PRETALX_API_TOKEN)
        self.speaker_gdrive_map = {}

        self.creds = None
        self.authorize_google()
        self.gdrive_service = build("drive", "v3", credentials=self.creds)
        self.gsheets_service = build("sheets", "v4", credentials=self.creds)
        self.speakers = {}

    def authorize_google(self):
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(self.creds.to_json())

    def get_gdrive_map(self):
        with open("speaker_gdrive_map.csv") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                self.speaker_gdrive_map[row[0]] = {"gdrive_id": row[1], "q_a": row[2]}

    def check_speaker_video(self, session):
        """Locate the speaker's GDrive folder, check if there's a video in it. Download the video, then check the duration."""
        results = (
            self.gdrive_service.files()
            .list(q=f"'{session.gdrive_id}' in parents", pageSize=10,  fields="nextPageToken, files(id, name)", corpora="user",)
            .execute()
        )
        items = results.get("files", [])
        for file in items:
            if file["name"].endswith(".mp4") or file["name"].endswith(".mkv") or file["name"].endswith(".mov"):
                print(f"Found video for {session.title} - {file['id']}")

                if not os.path.exists(f"speaker_videos/{file["name"]}"):
                    request = self.gdrive_service.files().get_media(fileId=file["id"])
                    file_handler = io.BytesIO()
                    downloader = MediaIoBaseDownload(file_handler, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                        print(f"Download {int(status.progress() * 100)}.")
                    print(f"File downloaded {file['name']}")
                    file_handler.seek(0)
                    with open(f"speaker_videos/{file["name"]}", "wb") as f:
                        f.write(file_handler.read())
                        f.close()

            else:
                print(f"Found unknown file in {session.title}, {session.gdrive_id}")

            video_length = get_audio_length(f"speaker_videos/{file['name']}")
            if video_length > MAX_SECONDS:
                print(f"WARNING video longer than 20 minutes: {session.title}")
                session.video_within_limit = False
            else:
                session.video_within_limit = True
            session.video_received = True
            session.video_length = video_length
            session.video_duration = timedelta(seconds=video_length)

    def generate_schedule(self):
        self.sessions = [Session(session) for session in self.pretalx_wrapper.get_submissions()]
        for session in self.sessions:
            for speaker in session.speakers:
                if speaker.speaker_id in self.speaker_gdrive_map:
                    session.gdrive_id = self.speaker_gdrive_map[speaker.speaker_id]["gdrive_id"]
                    session.q_a = self.speaker_gdrive_map[speaker.speaker_id]["q_a"]

        scheduled_sessions = sorted([session for session in self.sessions if session.start_time is not None], key=lambda s: s.start_time)

        for session in scheduled_sessions:
            if session.gdrive_id:
                self.check_speaker_video(session)
        session_rows = []
        with open("schedule.csv", "w") as f:
            writer = csv.writer(f)
            header = ["session_code", "title", "submission_type", "state", "room", "start_time", "end_time", "speakers", "gdrive_id", "video_received", "video_length", "video_duration", "video_within_limit", "q&a", "gdrive_url"]
            writer.writerow(header)
            session_rows.append(header)
            for session in scheduled_sessions:
                if session.room == MAIN_STREAM_ROOM:
                    writer.writerow(session.to_dict().values())
                    session_rows.append([v for v in session.to_dict().values()])
            unscheduled_sessions = [session for session in self.sessions if session.start_time is None]
            for session in unscheduled_sessions:
                writer.writerow(session.to_dict().values())
                session_rows.append([v for v in session.to_dict().values()])

        sheet = self.gsheets_service.spreadsheets()
        range = f"{SHEET_TAB}!A1:O{len(self.sessions)+1}"

        body = {
          "valueInputOption": "USER_ENTERED",
          "data": {
  "range": range,
  "values": session_rows
},
          "includeValuesInResponse": True,
        }
        result = (
            sheet.values()
            .batchUpdate(spreadsheetId=GSHEET_ID, body=body )
            .execute()
        )
        values = result.get("values", [])
        print(values)


def main():
    pyladiescon = PyLadiesCon()
    pyladiescon.get_gdrive_map()
    pyladiescon.generate_schedule()

if __name__ == "__main__":
    main()