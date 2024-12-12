import httpx
import base64
import os
import os.path

from textwrap import dedent
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from pathlib import Path
from email.message import EmailMessage


BASE_PRETIX_URL = "https://pretix.eu/api/v1/"
SCOPES = ["https://www.googleapis.com/auth/drive",
          "https://www.googleapis.com/auth/presentations",
"https://www.googleapis.com/auth/gmail.send"
          ]
PRETIX_API_TOKEN = ""

GSLIDES_TEMPLATE_ID = ""
GDRIVE_CERTIFICATES_FOLDER = ""
STATS_SHEETS_ID = ""

ITEM_ID_DONATION_ONLY = 655122
ITEM_ID_GENERAL_TICKET = 609703
ITEM_ID_SPEAKER_TICKET = 641803
ITEM_ID_SPONSOR_TICKET = 641804
ITEM_ID_DONATION_ADDON = 618597



class PretixWrapper:
    def __init__(self, token):
        self.headers = {"Authorization": f"Token {token}"}

    def get_orders(self):
        params = {}
        has_response = True
        url = BASE_PRETIX_URL + "organizers/pyladiescon/events/2024/orders/"
        index = 0
        while has_response:
            response = httpx.get(url, headers=self.headers, params=params)
            url = response.json()["next"]
            has_response = url is not None
            for r in response.json()["results"]:
                index += 1
                yield r

class PyLadiesCon:
    def __init__(self):
        self.pretix_wrapper = PretixWrapper(PRETIX_API_TOKEN)

        self.creds = None
        self.authorize_google()
        self.gdrive_service = build("drive", "v3", credentials=self.creds)
        self.gslides_service = build("slides", "v1", credentials=self.creds)
        self.gmail_service = build("gmail", "v1", credentials=self.creds)
        self.gsheets_service = build("sheets", "v4", credentials=self.creds)
        self.pretix_orders = 0
        self.pretix_proceeds = 0


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

    def copy_presentation(self, presentation_id, attendee_name):
        body = {"name": f"PyLadiesCon 2024 Certificate: {attendee_name}"}
        drive_response = (
            self.gdrive_service.files().copy(fileId=presentation_id, body=body).execute()
        )
        presentation_copy_id = drive_response.get("id")
        return presentation_copy_id

    def send_certificate_email(self, subject, sender_name, body_plain, body_html, sender_email, recipients, order_id, log_file=None):
        LOG_FILE = log_file or "email_sent_certificates.txt"

        if Path(LOG_FILE).exists():
            with open(LOG_FILE, "r") as rf:
                if order_id in rf.read():
                    print("WARN: An email was sent to that address already. Skipping")
                    return

        message = EmailMessage()
        message.set_content(body_plain)
        message.add_alternative(body_html, subtype="html")

        with open(f"./certificates/{order_id}.pdf","rb") as f:
            content = f.read()
            message.add_attachment(content, maintype="application", subtype="pdf", filename=f"{order_id}.pdf")


        message["Subject"] = subject
        message["From"] = f"{sender_name} <{sender_email}>"
        message["To"] = ", ".join(recipients)

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        recipients = recipients

        send_message = (
            self.gmail_service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )

        # Register who gets the email in case of emergency
        with open(LOG_FILE, "a") as f:
            f.write(order_id)
            f.write("\n")

    def generate_certificates(self):

        response = self.pretix_wrapper.get_orders()
        for order in response:

            if not order["testmode"]:
                items = order["positions"]

                payment_confirmed = False

                for payment in order["payments"]:
                    if payment["state"] == "confirmed":
                        payment_confirmed = True

                if payment_confirmed:
                    for item in items:
                        if item["item"] in [ITEM_ID_GENERAL_TICKET, ITEM_ID_SPEAKER_TICKET, ITEM_ID_SPONSOR_TICKET]:
                            order_position = f"{item['order']}-{item['positionid']}"
                            self.generate_certificate(order_position, item["attendee_name"])

                            body_plain = dedent(f"""
                            Dear {item['attendee_name']},
                            
                            
        Thank you for participating at PyLadiesCon. Attached is your Certificate of Participation for
        PyLadiesCon 2024 held from December 6th-December 8th, 2024.
       
        * Recap
        
        Check out our conference recap conference recap for a summary of what we've accomplished at this year's conference.
        
        https://conference.pyladies.com/news/pyladiescon-ends/
        
        Watch any missed talks on our YouTube Playlist.
        
        https://www.youtube.com/playlist?list=PLOItnwPQ-eHxWh6Af6xRuKprSk_OBU0cL
        
        
        * Post-Conference Survey
        
        We also would like to invite you to share feedback about the conference so that we
        can improve and make the next conference even better. Please take a few minutes to fill out this form.
        
        https://forms.gle/8TYAXnQAMz9GUPsA8
        
        * Stay in touch
        
        Get news about PyLadiesCon by following us across social media platforms, and by subscribing to our YouTube channel and RSS Feed.
        
        - Mastodon: https://fosstodon.org/@pyladiescon
        - BlueSky: https://bsky.app/profile/pyladiescon.bsky.social
        - Instagram: https://instagram.com/pyladiescon
        - LinkedIn: https://www.linkedin.com/company/pyladiescon
        - YouTube: https://www.youtube.com/@PyLadiesGlobal
        - RSS Feed: https://conference.pyladies.com/index.xml
    

        Use our hashtags: #PyLadiesCon and #PyLadies.
        
        PyLadiesCon Organizers
    """)

                            email_template = dedent(
            f"""\
            <p>
        Dear {item['attendee_name']},</p>


        <p>
        Thank you for participating at PyLadiesCon. Attached is your Certificate of Participation for
        PyLadiesCon 2024 held from December 6th-December 8th, 2024.
        </p>
        <p><b>Recap</b><p>
        <p>Check out our <a href="https://conference.pyladies.com/news/pyladiescon-ends/">conference recap</a> for a summary of what we've accomplished at this year's conference.
        Watch any missed talks on our <a href="https://www.youtube.com/playlist?list=PLOItnwPQ-eHxWh6Af6xRuKprSk_OBU0cL">YouTube Playlist</a>.</p>
        <p><b>Post-Conference Survey</b><p>
        <p>We also would like to invite you to share feedback about the conference so that we
        can improve and make the next conference even better. Please take a few minutes to fill out
        <a href="https://forms.gle/8TYAXnQAMz9GUPsA8"><b>this form</b></a>.
        </p>
        <p>
        <b>Stay in touch<b>
</p><p>
    Get news about PyLadiesCon by following us across social media platforms like <a href="https://fosstodon.org/@pyladiescon">Mastodon</a>,
    <a href="https://bsky.app/profile/pyladiescon.bsky.social">Bluesky</a>,
    <a href="https://instagram.com/pyladiescon">Instagram</a>,
    <a href="https://www.linkedin.com/company/pyladiescon">LinkedIn</a>, and by subscribing to our <a href="https://www.youtube.com/@PyLadiesGlobal">YouTube channel</a> 
     and <a href="https://conference.pyladies.com/index.xml">RSS Feed</a>.

Use our hashtags <b>#PyLadiesCon</b> and <b>#PyLadies</b>.
        </p>
        <p>

        PyLadiesCon Organizers
        </p>
        """
        )
                            print(item["attendee_email"])
                            self.send_certificate_email(f"Certificate of Attendance and Post-Conference Survey",
                                                        "PyLadiesCon Organizers",
                                                        body_plain=body_plain,
                                                        body_html=email_template, sender_email="pyladiescon@pyladies.com",
                                                        recipients=[item["attendee_email"]],
                                                        order_id=order_position)

    def generate_certificate(self, order_id, attendee_name, attendee_role=None):
        presentation = (
            self.gslides_service.presentations().get(presentationId=GSLIDES_TEMPLATE_ID).execute()
        )
        filename = f"{order_id}.pdf"
        if not os.path.exists(f"./certificates/{filename}"):
            slides = presentation.get("slides")
            presentation_id = self.copy_presentation(GSLIDES_TEMPLATE_ID, order_id)

            requests = [
                {
                    "replaceAllText": {
                        "containsText": {
                            "text": "{{attendee-name}}",
                            "matchCase": True,
                        },
                        "replaceText": attendee_name,
                    }
                },
            ]
            if attendee_role is not None:
                requests.append({"replaceAllText": {
                        "containsText": {
                            "text": "{{attendee-role}}",
                            "matchCase": True,
                        },
                        "replaceText": attendee_role,
                    }

                })
            body = {"requests": requests}
            response = self.gslides_service.presentations().batchUpdate(presentationId=presentation_id,
                                                                        body=body).execute()
            stream = self.gdrive_service.files().export(fileId=presentation_id, mimeType="application/pdf").execute()
            with open(f"./certificates/{filename}", "wb") as f:
                f.write(stream)

    def generate_volunteer_speaker_certificates(self):
        sheet = self.gsheets_service.spreadsheets()
        result = (
        sheet.values()
        .get(spreadsheetId=STATS_SHEETS_ID, range="Certificate generation!A2:D200")
        .execute()
    )
        values = result.get("values", [])
        for row in values:
            name = row[0]
            email = row[1]
            role = row[2]
            id = f"{role}-{name}"
            self.generate_certificate(id, name, role)
            body_plain = dedent(f"""
                                        Dear {name},


                    Thank you for being a {role} at PyLadiesCon. Attached is your Certificate of Participation for
                    PyLadiesCon 2024 held from December 6th-December 8th, 2024.


                    PyLadiesCon Organizers
                """)

            email_template = dedent(
                f"""\
                        <p>
                    Dear {name},</p>


                    <p>
                    Thank you for being a {role} at PyLadiesCon. Attached is your Certificate of Participation for
                    PyLadiesCon 2024 held from December 6th-December 8th, 2024.
                    </p>
                    
                    <p>

                    PyLadiesCon Organizersq
                    </p>
                    """
            )
            print(email)
            self.send_certificate_email(f"Thank you for being a {role} at PyLadiesCon",
                                        "PyLadiesCon Organizers",
                                        body_plain=body_plain,
                                        body_html=email_template, sender_email="pyladiescon@pyladies.com",
                                        recipients=[email],
                                        order_id=id)



if __name__ == "__main__":
    util = PyLadiesCon()
    util.generate_volunteer_speaker_certificates()



