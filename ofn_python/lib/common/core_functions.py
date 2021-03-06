import gspread
import os
import pandas as pd
import smtplib

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.discovery import build


SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_data_from_google_sheet(
    credentials_file, filename, columns, worksheet_name=None
):
    """Get data from Google sheet."""
    CREDENTIALS_FILE = f'{os.environ["PATH_TO_OFN_PYTHON"]}/creds/{credentials_file}'
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open(filename)

    if not worksheet_name:
        worksheet_list = sheet.worksheets()
        data = pd.DataFrame()
        for worksheet in worksheet_list:
            sheet_df = pd.DataFrame(worksheet.get_all_records())
            try:
                sheet_df = sheet_df[columns]
            except KeyError:
                sheet_df = pd.DataFrame(columns=columns)
            data = data.append(sheet_df, ignore_index=True)

    else:
        worksheet = sheet.worksheet(worksheet_name)
        data = pd.DataFrame(worksheet.get_all_records())
        try:
            data = data[columns]
        except KeyError:
            data = pd.DataFrame(columns=columns)

    return data, sheet


def store_to_gdrive(credentials_file, folder_id, filename, mimetype, fh):
    """Function to upload file to google drive."""
    CREDENTIALS_FILE = f'{os.environ["PATH_TO_OFN_PYTHON"]}/creds/{credentials_file}'
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
    service = build("drive", "v3", credentials=creds)
    body = {"name": filename, "mimeType": mimetype, "parents": [folder_id]}
    media_body = MediaIoBaseUpload(fh, mimetype=mimetype, resumable=True)
    service.files().create(body=body, media_body=media_body).execute()


def send_email(
    receivers,
    subject,
    body,
    filename=None,
    attchmnt=None,
    file_extension="xml",
    cc=None,
):
    """General send email function."""
    smtp_server = os.environ.get("SMTP_SERVER")
    port = 465
    sender_email = os.environ.get("SMTP_SERVER_USER")
    password = os.environ.get("SMTP_SERVER_PASSWORD")

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(receivers)
    if cc:
        message["CC"] = ", ".join(cc)
        toaddr = receivers + cc
    else:
        toaddr = receivers
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    if attchmnt:
        attachment = MIMEBase("application", file_extension)
        attachment.set_payload(attchmnt)
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            f"attachment; filename= {filename}",
        )
        message.attach(attachment)

    text = message.as_string()
    with smtplib.SMTP_SSL(smtp_server, port) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, toaddr, text)
