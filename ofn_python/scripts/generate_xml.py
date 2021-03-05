from ofn_python.lib.xml_orders import XMLOrder

import datetime as dt
import os
import gspread
import pandas as pd
import requests

from oauth2client.service_account import ServiceAccountCredentials


SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]
CREDENTIALS_FILE = f'{os.environ["PATH_TO_OFN_PYTHON"]}/creds/openfoodnetwork-9e79b28ba490.json'


def get_data_from_google_sheet(filename, columns):
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open(filename)
    worksheet_list = sheet.worksheets()

    data = pd.DataFrame()
    for worksheet in worksheet_list:
        sheet_df = pd.DataFrame(worksheet.get_all_records())
        try:
            sheet_df = sheet_df[columns]
        except KeyError:
            sheet_df = pd.DataFrame(columns=columns)
        data = data.append(sheet_df, ignore_index=True)

    return data


def run():
    today = dt.datetime.today().date()
    url = f'https://openfoodnetwork.de/api/orders?q[completed_at_gt]={today}&q[state_eq]=complete&q[distributor_name_eq]=Münsterländer Bauernbox eG (iG) '
    headers = {
        'Accept': 'application/json;charset=UTF-8',
        'Content-Type': 'application/json'
    }
    params = (('token', os.environ['OPENFOODNETWORK_API_KEY']),)
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data['orders']:
        orders = pd.json_normalize(data['orders']).sort_values('id').reset_index(drop=True)
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        worksheet = client.open('Bauernbox Übersicht').sheet1
        all_records = worksheet.get_all_records()
        sheet_df = pd.DataFrame(all_records)
        orders = orders[~orders['number'].isin(sheet_df['number'].tolist())].reset_index(drop=True)

        if not orders.empty:
            orders = orders[['id', 'number', 'user_id', 'full_name', 'email', 'phone',
            'completed_at', 'display_total', 'edit_path', 'state', 'payment_state',
            'shipment_state', 'payments_path', 'ready_to_ship', 'created_at',
            'distributor_name', 'special_instructions', 'display_outstanding_balance', 'item_total',
            'adjustment_total', 'payment_total', 'total', 'distributor.id', 'order_cycle.id']]

            orders.rename(columns={'distributor.id': 'distributor_id',
                'order_cycle.id': 'order_cycle_id'}, inplace=True)

            ofn_server_name = 'https://openfoodnetwork.de'
            eans = get_data_from_google_sheet('Produktliste_MSB_XXX_Artikelstammdaten',
                ['sku', 'tax_category', 'EAN'])
            postal_codes = ['48143', '48147', '48145', '48157', '48159', '48151', '48155', '48153',
            '48161', '48167', '48165', '48163', '48149']

            for i in orders.itertuples():
                print(i.number, i.full_name, i.total, i.completed_at)
                xml_order = XMLOrder(ofn_server_name)
                xml_order.generate(i.number, headers, params, eans, postal_codes)
                orders.at[i.Index, 'xml_generated_at'] = dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                print('---')

            orders['payments_path'] = orders['payments_path'].apply(lambda x: ofn_server_name + x)
            orders['edit_path'] = orders['edit_path'].apply(lambda x: ofn_server_name + x)
            orders['created_at'] = orders['created_at'].apply(lambda x: dt.datetime.strptime(x,
                '%B %d, %Y').strftime('%Y-%m-%d'))
            orders['completed_at'] = orders['completed_at'].apply(lambda x:
                dt.datetime.strptime(x, '%B %d, %Y').strftime('%Y-%m-%d'))
            orders['ready_to_capture'] = ''
            orders = orders[['id', 'number', 'user_id', 'full_name', 'email', 'phone',
            'completed_at', 'display_total', 'edit_path', 'state', 'payment_state',
            'shipment_state', 'payments_path', 'ready_to_ship', 'ready_to_capture',
            'created_at', 'distributor_name', 'special_instructions',
            'display_outstanding_balance','item_total', 'adjustment_total', 'payment_total',
            'total', 'distributor_id', 'order_cycle_id', 'xml_generated_at']]

            # Save new orders to Bauernbox Übersicht google table
            orders.fillna('', inplace=True)
            orders_lol = orders.values.tolist()
            worksheet.append_rows(orders_lol)


if __name__ == '__main__':
    run()
