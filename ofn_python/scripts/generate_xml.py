import datetime as dt
import os
import pandas as pd
import requests

from ofn_python.lib.common.core_functions import get_data_from_google_sheet
from ofn_python.lib.xml_orders import XMLOrder


def run():
    today = dt.datetime.today().date()
    server_name = 'https://openfoodnetwork.de'
    distributor_name = 'Bauernbox - Münster  (Münsterländer Bauernbox eG (iG) )'
    url = f'{server_name}/api/orders?q[completed_at_gt]={today}&q[state_eq]=complete&q[distributor_name_eq]={distributor_name}'
    headers = {
        'Accept': 'application/json;charset=UTF-8',
        'Content-Type': 'application/json'
    }
    params = (('token', os.environ['OPENFOODNETWORK_API_KEY']),)
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data['orders']:
        orders = pd.json_normalize(data['orders']).sort_values('id').reset_index(drop=True)
        order_nos, sheet = get_data_from_google_sheet('Bauernbox Übersicht', ['number'])
        orders = orders[~orders['number'].isin(order_nos['number'].tolist())].reset_index(drop=True)

        if not orders.empty:
            orders = orders[['id', 'number', 'user_id', 'full_name', 'email', 'phone',
            'completed_at', 'display_total', 'edit_path', 'state', 'payment_state',
            'shipment_state', 'payments_path', 'ready_to_ship', 'created_at',
            'distributor_name', 'special_instructions', 'display_outstanding_balance', 'item_total',
            'adjustment_total', 'payment_total', 'total', 'distributor.id', 'order_cycle.id']]

            orders.rename(columns={'distributor.id': 'distributor_id',
                'order_cycle.id': 'order_cycle_id'}, inplace=True)

            for order in orders.itertuples():
                print(order.number, order.full_name, order.total, order.completed_at)
                xml_order = XMLOrder(order.number)
                xml_order.generate()
                orders.at[order.Index, 'xml_generated_at'] = dt.datetime.now().strftime(
                    '%Y-%m-%dT%H:%M:%S')
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
            worksheet = sheet.worksheet('münster')
            orders.fillna('', inplace=True)
            worksheet.append_rows(orders.values.tolist())


if __name__ == '__main__':
    run()
