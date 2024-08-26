# Sending email and generating certificates

## Local environment setup

1. Create and activate the virtual environment, e.g.

```
python3 -m venv venv
source venv/bin/activate
```

2. Install the dependencies

```[2023_participants_test.csv](..%2F..%2F..%2F..%2FDownloads%2Fcertificate-gen%2F2023_participants_test.csv)
python3 -m pip install -U pip
python3 -m pip install -r requirements.txt
```
## Email address list

Create the email address as a csv file. See example in ``2023_participants_test.csv``.


## Generating certificates

1. Run the ``gen_certificates.py`` script. You may need to adjust the file/filename containing the csv before running
   the script.


## Sending email

1. First ensure the certificates have been generated.
2. Get GMail OAuth credentials: https://developers.google.com/workspace/guides/configure-oauth-consent
3. Download the ``credentials.json`` file and add to the same directory where ``email_sender.py`` is located.
4. Run the script against a test email first, and verify the content, before sending a mass email.

