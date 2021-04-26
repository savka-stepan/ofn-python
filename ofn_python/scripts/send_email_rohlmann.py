import datetime as dt
import json
import io
import os
import pandas as pd
import requests

from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import mm

from ofn_python.lib.common.core_functions import send_email
from ofn_python.lib.common.core import OFNData


def run():
    today = dt.datetime.today().date()
    server_name = 'https://openfoodnetwork.de'
    headers = {
        'Accept': 'application/json;charset=UTF-8',
        'Content-Type': 'application/json'
    }
    params = (('token', os.environ['OPENFOODNETWORK_API_KEY']),)

    url = f'{server_name}/api/orders?q[completed_at_gt]={today}&q[state_eq]=complete&q[distributor_id_eq]=36'
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data['orders']:
        orders = pd.json_normalize(data['orders']).sort_values('id').reset_index(drop=True)
        orders = orders[['number',]]

        stream_kr = io.BytesIO()
        stream_tb = io.BytesIO()
        doc_kr = SimpleDocTemplate(stream_kr, pagesize=A4, rightMargin=18, leftMargin=18,
            topMargin=18, bottomMargin=18)
        doc_tb = SimpleDocTemplate(stream_tb, pagesize=A4, rightMargin=18, leftMargin=18,
            topMargin=18, bottomMargin=18)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='align_right', alignment=TA_RIGHT))

        body_kr = []
        body_tb = []
        is_kr = False
        is_tb = False
        for order in orders.itertuples():
            print(order.number)

            p1 = Paragraph(f'<font size="8"><b>Product name</b></font>', styles["Normal"])
            p2 = Paragraph(f'<font size="8"><b>SKU</b></font>', styles["align_right"])
            p3 = Paragraph(f'<font size="8"><b>Qty</b></font>', styles["align_right"])
            p4 = Paragraph(f'<font size="8"><b>Price</b></font>', styles["align_right"])
            data_kr = [[p1, p2, p3, p4]]
            data_tb = [[p1, p2, p3, p4]]

            ofn_data = OFNData(server_name, headers, params)
            ofn_data.get_order_data(order.number)

            for item in ofn_data.order_data['line_items']:
                ofn_data.get_product_data(item['variant']['product_name'])

                try:
                    product = ofn_data.product_data['products'][0]
                except IndexError:
                    product = None

                if product:
                    if product['master']['producer_name'] == 'Kräuterhof Rohlmann ':
                        print('Kräuterhof Rohlmann', item["variant"]["product_name"], item["quantity"], item["price"])
                        p1 = Paragraph(f'<font size="8">{item["variant"]["product_name"]} {item["variant"]["unit_to_display"]}</font>', styles["Normal"])
                        p2 = Paragraph(f'<font size="8">{item["variant"]["sku"]}</font>', styles["align_right"])
                        p3 = Paragraph(f'<font size="8">{item["quantity"]}</font>', styles["align_right"])
                        p4 = Paragraph(f'<font size="8">{item["price"]}</font>', styles["align_right"])
                        data_kr.append([p1, p2, p3, p4])

                    elif product['master']['producer_name'] == 'Tollkötter Bäckerei ':
                        print('Tollkötter Bäckerei', item["variant"]["product_name"], item["quantity"], item["price"])
                        p1 = Paragraph(f'<font size="8">{item["variant"]["product_name"]} {item["variant"]["unit_to_display"]}</font>', styles["Normal"])
                        p2 = Paragraph(f'<font size="8">{item["variant"]["sku"]}</font>', styles["align_right"])
                        p3 = Paragraph(f'<font size="8">{item["quantity"]}</font>', styles["align_right"])
                        p4 = Paragraph(f'<font size="8">{item["price"]}</font>', styles["align_right"])
                        data_tb.append([p1, p2, p3, p4])

            if len(data_kr) > 1:
                body_kr.append(Paragraph(f'<font size="12">Order {order.number}</font>', styles["Normal"]))
                body_kr.append(Spacer(1, 12))

                t_kr = Table(data_kr, colWidths=(96*mm, 31*mm, 31*mm, 31*mm))
                t_kr.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), '#e8e8e8'),
                    ('BOX', (0, 0), (-1, -1), 0.25, '#000000'),
                    ('LINEBELOW', (0, 0), (-1, -2), 0.25, '#000000')
                ]))
                body_kr.append(t_kr)
                body_kr.append(Spacer(1, 24))
                is_kr = True

            if len(data_tb) > 1:
                body_tb.append(Paragraph(f'<font size="12">Order {order.number}</font>', styles["Normal"]))
                body_tb.append(Spacer(1, 12))

                t_tb = Table(data_tb, colWidths=(96*mm, 31*mm, 31*mm, 31*mm))
                t_tb.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), '#e8e8e8'),
                    ('BOX', (0, 0), (-1, -1), 0.25, '#000000'),
                    ('LINEBELOW', (0, 0), (-1, -2), 0.25, '#000000')
                ]))
                body_tb.append(t_tb)
                body_tb.append(Spacer(1, 24))
                is_tb = True

        doc_kr.build(body_kr)
        pdf_file_kr = stream_kr.getvalue()
        stream_kr.close()

        doc_tb.build(body_tb)
        pdf_file_tb = stream_tb.getvalue()
        stream_tb.close()

        if is_kr:
            send_email(os.environ['EMAIL_OFN'], "Kräuterhof Rohlmann today's items", '',
                'KrauterhofRohlmann.pdf', pdf_file_kr, file_extension='pdf')
        if is_tb:
            send_email(os.environ['EMAIL_OFN'], "Tollkötter Bäckerei today's items", '',
                'TollkotterBackerei.pdf', pdf_file_tb, file_extension='pdf')

if __name__ == '__main__':
    run()
