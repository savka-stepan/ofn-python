# import datetime as dt
import ftplib
import io
import os
# import pandas as pd
import requests

from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate

from ofn_python.lib.common.core_functions import get_data_from_google_sheet
from ofn_python.lib.pdf_invoices import InvoiceNo, PDFInvoice


def run():

    order_nos = get_data_from_google_sheet('Bauernbox Übersicht', ['number'])
    print(order_nos)

    # server_name = 'https://openfoodnetwork.de'

    # shop_url = f'{server_name}/api/shops/36'
    # headers = {
    #     'Accept': 'application/json;charset=UTF-8',
    #     'Content-Type': 'application/json'
    # }
    # params = (('token', os.environ['OPENFOODNETWORK_API_KEY']),)
    # response = requests.get(shop_url, headers=headers, params=params)
    # shop_data = response.json()

    # init_invoice_no = InvoiceNo('RE-0000000')
    # invoice_no = init_invoice_no.get_next_invoice_no()

    # order_url = f'{server_name}/api/orders/R606118335'
    # response = requests.get(order_url, headers=headers, params=params)
    # order_data = response.json()

    # stream = io.BytesIO()
    # doc = SimpleDocTemplate(stream, pagesize=A4, rightMargin=18, leftMargin=18, topMargin=18,
    #     bottomMargin=18)
    # styles = getSampleStyleSheet()
    # styles.add(ParagraphStyle(name='align_right', alignment=TA_RIGHT))

    # pdf_invoice = PDFInvoice(invoice_no, shop_data, order_data)
    # pdf_invoice.generate(styles)

    # doc.build(pdf_invoice.body)
    # result = stream.getvalue()
    # stream.close()

    # with ftplib.FTP(os.environ['FTP_SERVER'], os.environ['FTP_USERNAME'],
    #         os.environ['FTP_PASSWORD']) as ftp:
    #     ftp.storbinary(f'STOR invoices/invoice{invoice_no}.pdf', io.BytesIO(result))


if __name__ == '__main__':
    run()
