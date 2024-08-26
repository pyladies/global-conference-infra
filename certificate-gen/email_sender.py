import base64
import mimetypes
import sys
import pandas as pd
import os.path

from email.message import EmailMessage

from pathlib import Path
from textwrap import dedent

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


sender_name = "PyLadiesCon"
sender_email = "pyladiescon@pyladies.com"


def attach_pdf_to_email(message, pdf_file):
    with open(pdf_file, "rb") as pdf:
        data = pdf.read()
        maintype, _, subtype = (
            mimetypes.guess_type(pdf_file)[0] or "application/octet-stream"
        ).partition("/")
        message.add_attachment(data, maintype=maintype, subtype=subtype, filename=pdf_file)



def send_email(subject, body, sender_name, sender_email, recipients, pdf_file):
    # configure Google OAuth: https://developers.google.com/workspace/guides/configure-oauth-consent
    # We need to have "credentials.json" downloaded from the Google Workspace

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
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())


    # Check if email was sent
    LOG_FILE = "email_sent.txt"

    if Path(LOG_FILE).exists():
        with open("email_sent.txt", "r") as rf:
            if ", ".join(recipients) in rf.read():
                print("WARN: An email was sent to that address already. Skipping")
                return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{sender_name} <{sender_email}>"
    message["To"] = ", ".join(recipients)
    message.set_content(body)
    attach_pdf_to_email(message, pdf_file)

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {"raw": encoded_message}

    service = build("gmail", "v1", credentials=creds)
    send_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )

    # Register who gets the email in case of emergency
    with open("email_sent.txt", "a") as f:
        f.write(", ".join(recipients))
        f.write("\n")


if __name__ == "__main__":

    # Read file
    # TODO: Using test first
    # df = pd.read_csv("2023_participants.csv")
    df = pd.read_csv("2023_participants_test.csv")

    df.fillna('', inplace=True)
    for idx, row in df.iterrows():
        name = f"{row['First Name']} {row['Last Name']}"
        email = row["Email"]
        pdf_file = f'out/{name.lower().replace(" ", "_")}.pdf'
        if not Path(pdf_file).exists():
            print(f"Error: no certificate for '{name}'")
            sys.exit(-1)

        body = dedent(
            f"""\
        Hey there, {name}!

        You can find your attached Certificate of Participation from PyLadiesCon 2023.

        PyLadiesCon is back in 2024! If you enjoyed the 2023 version, we
        kindly invite you to make this year an even better conference!
                
        1. Our CFP is open.
        
        Our Call for proposals is open until September 15th, so we hope to see
        your proposal! If you know of another PyLady who you think would be a great speaker, please
        let them know about this opportunity and ask them to submit a talk!
        
        https://pretalx.com/pyladiescon-2024/cfp

        2. Learn more.
        
        Help us to make this a real global conference by having talks from all
        over the world, with representation from the global PyLadies chapters and community members.
        
        Our website now features a blog and RSS feed so that you can stay up to date with our news. Check it
        out for more information about the conference, sponsorship, and volunteering opportunities.
        
        https://conference.pyladies.com
        
        3. Stay connected.
        
        Stay in touch and connect with us on social media:
        
        - LinkedIn: https://www.linkedin.com/company/pyladiescon
        - Mastodon: https://fosstodon.org/@pyladiescon
        - Twitter/X: https://twitter.com/pyladiescon
        - Instagram: https://instagram.com/pyladiescon

        PyLadiesCon Organizers
        """
        )
        recipients = [email]
        subject = "[PyLadiesCon] 2023 Certificate of attendance + 2024 Conference Launch"

        # DANGER: remove comment only when ready to send!
        #send_email(subject, body, sender_name, sender_email, recipients, pdf_file)
        # END DANGER

        # Comment this when ready to send all the messages
        print(f"From: {sender_name} {sender_email}")
        print(f"To: {name} {recipients}")
        print("Subject: {subject}")
        print()
        print(body)
        input()
