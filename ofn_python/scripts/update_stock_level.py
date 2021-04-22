import ftplib
import pandas as pd
import requests
import io
import os


def run():
    server_name = 'https://openfoodnetwork.de'
    headers = {
        'Accept': 'application/json;charset=UTF-8',
        'Content-Type': 'application/json'
    }
    params = (('token', os.environ['OPENFOODNETWORK_API_KEY']),)

    # result = None
    # with ftplib.FTP(os.environ['FTP_SERVER'], os.environ['FTP_USERNAME'],
    #     os.environ['FTP_PASSWORD']) as ftp:
    #     result = io.BytesIO()
    #     ftp.retrbinary('RETR stock/lagerbestand.bst', result.write)

    # if result:
    #     data_str = str(result.getvalue(), 'utf-8')
    #     data = io.StringIO(data_str)
    #     data_df = pd.read_csv(data, sep=r'\s+', names=['sku', 'qty', 'type'])
    #     data_df = data_df.loc[data_df['sku'].str.contains('MSB')]

        # for i in data_df[:1].itertuples():
        #     print(i.sku, i.qty)
        #     url = f'{server_name}/api/products/bulk_products/variants?q[sku_eq]={i.sku}'
        #     response = requests.get(url, headers=headers, params=params)
        #     items = response.json()

        #     if items:
        #         print(items)
        #         for item in items:
        #             item_url = f'{server_name}/api/products/bulk_products/variants?q[id_eq]={item["id"]}'
        #             response = requests.get(url, headers=headers, params=params)
        #             print(response.json())
        #             # response = requests.put(url, headers=headers, params=params, json={'product': {'on_hand': i.qty}})


if __name__ == '__main__':
    run()
