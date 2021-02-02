import datetime as dt
import gspread
import json
import os
import re
import requests
import pandas as pd
import xml.etree.ElementTree as ET

from oauth2client.service_account import ServiceAccountCredentials


SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]
CREDENTIALS_FILE = f'{os.environ["PATH_TO_OFN_PYTHON"]}/creds/openfoodnetwork-9e79b28ba490.json'


def update_stock_qty(worksheet, sheet_df, variants):
    for s in sheet_df.itertuples():
        found_sku = variants.loc[variants['sku'] == sheet_df.at[s.Index, 'sku']]
        if not found_sku.empty:
            print(s.sku)

            on_hand = found_sku.iloc[0]['on_hand']
            if s.on_hand != on_hand:
                cell = worksheet.find(s.sku)
                worksheet.update_cell(cell.row, 11, int(on_hand))
                print(f'Old stock qty = {s.on_hand}')
                print(f'New stock qty = {on_hand}')
            else:
                print('Same stock qty')

            print('===')


def get_and_write_new_items(data, sheet_df, worksheet):
    variants = pd.DataFrame()
    for product in data['products']:
        temp = pd.json_normalize(product['variants'])[['producer_name', 'sku', 'name',
        'display_name', 'unit_value', 'unit_to_display', 'price', 'on_hand', 'on_demand']]
        temp['variant_unit'] = product['variant_unit']
        temp['available_on'] = product['available_on']
        res_df = pd.concat([variants, temp], sort=False).reset_index(drop=True)
        variants = res_df

    # Update on_hand and on_demand for already exist variants
    if worksheet.cell(1, 11).value == 'on_hand':
        update_stock_qty(worksheet, sheet_df, variants)

    variants = variants[~variants['sku'].isin(sheet_df['sku'].tolist())].reset_index(drop=True)

    if not variants.empty:
        variants['category'] = ''
        variants['description'] = ''
        variants['unit_to_display'] = variants['unit_to_display'].apply(lambda x:
            re.sub(r'\d+', '', x))
        variants['shipping_category'] = ''
        variants['tax_category'] = ''
        variants['EAN'] = ''

        variants = variants[['producer_name', 'sku', 'name', 'display_name', 'category',
        'description', 'unit_value', 'unit_to_display', 'variant_unit', 'price',
        'on_hand', 'available_on', 'on_demand', 'shipping_category', 'tax_category', 'EAN']]

        print(variants)

        variants.fillna('', inplace=True)
        variants_lol = variants.values.tolist()
        worksheet.append_rows(variants_lol)


def run():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open('Produktliste_MSB_XXX_Artikelstammdaten')
    worksheet_list = sheet.worksheets()

    for worksheet in worksheet_list:
        if worksheet.title != 'MSB-Geschenkeboxen':
            print(worksheet.title)
            sheet_df = pd.DataFrame(worksheet.get_all_records())
            try:
                sheet_df = sheet_df[['producer', 'sku', 'name', 'display_name', 'category',
                'description', 'units', 'unit_type', 'variant_unit_name', 'price', 'on_hand',
                'available_on', 'on_demand']]
            except KeyError:
                sheet_df = pd.DataFrame()

            if not sheet_df.empty:
                sheet_df['sku'] = sheet_df['sku'].apply(lambda x: str(x))
                producer = sheet_df.at[0, 'producer']

                url = f'https://openfoodnetwork.de/api/products/bulk_products?q[supplier_name_cont]={producer}&per_page=100'
                headers = {
                    'Accept': 'application/json;charset=UTF-8',
                    'Content-Type': 'application/json'
                }
                params = (('token', os.environ['OPENFOODNETWORK_API_KEY']),)
                response = requests.get(url, headers=headers, params=params)
                data = response.json()

                if data['products']:
                    get_and_write_new_items(data, sheet_df, worksheet)

                    if len(data['products']) == 100:
                        pages_count = data['pagination']['pages'] + 1

                        for i in range(2, pages_count):
                            url = f'https://openfoodnetwork.de/api/products/bulk_products?q[supplier_name_cont]={producer}&per_page=100&page={i}'
                            response = requests.get(url, headers=headers, params=params)
                            data_i = response.json()

                            if data_i['products']:
                                get_and_write_new_items(data_i, sheet_df, worksheet)

            print('---')
