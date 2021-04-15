import gspread
import os
import pandas as pd

from oauth2client.service_account import ServiceAccountCredentials


SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]


def get_data_from_google_sheet(credentials_file, filename, columns, worksheet_name=None):
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
