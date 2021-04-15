import datetime as dt
import os
import pandas as pd
import requests
import xml.etree.ElementTree as ET

from ofn_python.lib.common.core_functions import get_data_from_google_sheet
from ofn_python.lib.xml_orders import XMLOrder


def run(distributors):
    today = dt.datetime.today().date()
    yesterday = (dt.datetime.today() - dt.timedelta(days=1)).date()
    server_name = 'https://openfoodnetwork.de'
    headers = {
        'Accept': 'application/json;charset=UTF-8',
        'Content-Type': 'application/json'
    }
    params = (('token', os.environ['OPENFOODNETWORK_API_KEY']),)

    for distributor_id in distributors:
        if distributor_id == 132:
            credentials_file = 'openfoodnetwork-294510-e48e44a05ba0.json'
            worksheet_name = 'everswinkel'
            selected_date = today - dt.timedelta(days=7)
        elif distributor_id == 133:
            credentials_file = 'openfoodnetwork-294510-e48e44a05ba0.json'
            worksheet_name = 'rinkerode'
            selected_date = today - dt.timedelta(days=7)
        elif distributor_id == 139:
            credentials_file = 'openfoodnetwork-294510-32df7a510d34.json'
            worksheet_name = 'lieferbox'
            selected_date = yesterday
        else:
            credentials_file = 'openfoodnetwork-9e79b28ba490.json'
            worksheet_name = 'münster'
            selected_date = yesterday

        url = f'{server_name}/api/orders?q[completed_at_gt]={selected_date}&q[state_eq]=complete&q[distributor_id_eq]={distributor_id}'
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        # if (dt.datetime.now() >= dt.datetime.strptime('2021-03-31 19:35', '%Y-%m-%d %H:%M') and
        #     dt.datetime.now() <= dt.datetime.strptime('2021-03-31 20:05', '%Y-%m-%d %H:%M')):

        #     sheet_df, sheet = get_data_from_google_sheet(credentials_file, 'Bauernbox Übersicht', ['number',
        #         'order_cycle_id', 'xml_generated_at'], worksheet_name)
        #     worksheet = sheet.worksheet(worksheet_name)
        #     prev_orders = sheet_df.loc[(sheet_df['order_cycle_id'] == 323) & (sheet_df['xml_generated_at'] == '')]

        #     if not prev_orders.empty:
        #         for order in prev_orders.itertuples():
        #             print(order.number)

        #             xml_order = XMLOrder(order.number)
        #             xml_order.generate()
        #             filename = f"opentransorder{order.number}.xml"
        #             tree = ET.ElementTree(ET.fromstring(xml_order.xml_str, ET.XMLParser(encoding='utf-8')))
        #             root = tree.getroot()
        #             attchmnt = ET.tostring(root, encoding='utf-8', method='xml')
        #             xml_order.send_by_email(filename, attchmnt)
        #             xml_order.send_to_ftp_server(filename, attchmnt)

        #             cell = worksheet.find(order.number)
        #             worksheet.update_cell(cell.row, 26, dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))

        #             print('---')

        # if (dt.datetime.now() >= dt.datetime.strptime('2021-04-01 13:35', '%Y-%m-%d %H:%M') and
        #     dt.datetime.now() <= dt.datetime.strptime('2021-04-01 14:05', '%Y-%m-%d %H:%M')):

        #     sheet_df, sheet = get_data_from_google_sheet(credentials_file, 'Bauernbox Übersicht', ['number',
        #         'order_cycle_id', 'xml_generated_at'], worksheet_name)
        #     worksheet = sheet.worksheet(worksheet_name)
        #     prev_orders = sheet_df.loc[(sheet_df['order_cycle_id'] == 326) & (sheet_df['xml_generated_at'] == '')]

        #     if not prev_orders.empty:
        #         for order in prev_orders.itertuples():
        #             print(order.number)

        #             xml_order = XMLOrder(order.number)
        #             xml_order.generate()
        #             filename = f"opentransorder{order.number}.xml"
        #             tree = ET.ElementTree(ET.fromstring(xml_order.xml_str, ET.XMLParser(encoding='utf-8')))
        #             root = tree.getroot()
        #             attchmnt = ET.tostring(root, encoding='utf-8', method='xml')
        #             xml_order.send_by_email(filename, attchmnt)
        #             xml_order.send_to_ftp_server(filename, attchmnt)

        #             cell = worksheet.find(order.number)
        #             worksheet.update_cell(cell.row, 26, dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))

        #             print('---')

        if data['orders']:
            orders = pd.json_normalize(data['orders']).sort_values('id').reset_index(drop=True)
            order_nos, sheet = get_data_from_google_sheet(credentials_file, 'Bauernbox Übersicht',
                ['number'], worksheet_name)
            orders = orders[~orders['number'].isin(order_nos['number'].tolist())].reset_index(
                drop=True)

            if not orders.empty:
                orders = orders[['id', 'number', 'user_id', 'full_name', 'email', 'phone',
                'completed_at', 'display_total', 'edit_path', 'state', 'payment_state',
                'shipment_state', 'payments_path', 'ready_to_ship', 'created_at',
                'distributor_name', 'special_instructions', 'display_outstanding_balance',
                'item_total', 'adjustment_total', 'payment_total', 'total', 'distributor.id',
                'order_cycle.id']]

                orders.rename(columns={'distributor.id': 'distributor_id',
                    'order_cycle.id': 'order_cycle_id'}, inplace=True)

                eans = get_data_from_google_sheet(credentials_file,
                    'Produktliste_MSB_XXX_Artikelstammdaten', ['sku', 'EAN'])[0]
                postal_codes = ['48143', '48147', '48145', '48157', '48159', '48151', '48155',
                '48153', '48161', '48167', '48165', '48163', '48149']

                for order in orders.itertuples():
                    print(order.number, order.full_name, order.total, order.completed_at)

                    if order.order_cycle_id not in (323, 326):
                        xml_order = XMLOrder(server_name, headers, params, order.number, eans,
                            postal_codes)
                        xml_order.generate()
                        filename = f"opentransorder{order.number}.xml"
                        tree = ET.ElementTree(ET.fromstring(xml_order.xml_str, ET.XMLParser(encoding='utf-8')))
                        root = tree.getroot()
                        attchmnt = ET.tostring(root, encoding='utf-8', method='xml')
                        xml_order.send_by_email(filename, attchmnt)
                        xml_order.send_to_ftp_server(filename, attchmnt)

                        orders.at[order.Index, 'xml_generated_at'] = dt.datetime.now().strftime(
                            '%Y-%m-%dT%H:%M:%S')

                    else:
                        orders.at[order.Index, 'xml_generated_at'] = ''
                    
                    print('---')

                orders['payments_path'] = orders['payments_path'].apply(lambda x: server_name + x)
                orders['edit_path'] = orders['edit_path'].apply(lambda x: server_name + x)
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
                worksheet = sheet.worksheet(worksheet_name)
                orders.fillna('', inplace=True)
                worksheet.append_rows(orders.values.tolist())


if __name__ == '__main__':
    run()
