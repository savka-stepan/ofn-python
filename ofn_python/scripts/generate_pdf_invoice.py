import datetime as dt
import io
import os
import pandas as pd
import requests

from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm

from ofn_python.lib.pdf_invoices import InvoiceNo, PDFInvoice


def run():

    server_name = 'https://openfoodnetwork.de'

    shop_url = f'{server_name}/api/shops/36'
    headers = {
        'Accept': 'application/json;charset=UTF-8',
        'Content-Type': 'application/json'
    }
    params = (('token', os.environ['OPENFOODNETWORK_API_KEY']),)
    response = requests.get(shop_url, headers=headers, params=params)
    shop_data = response.json()

    init_invoice_no = InvoiceNo('RE-0000000')
    invoice_no = init_invoice_no.get_next_invoice_no()

    order_url = f'{server_name}/api/orders/R861780311'
    response = requests.get(order_url, headers=headers, params=params)
    order_data = response.json()
    
    doc = SimpleDocTemplate(f'invoice{invoice_no}.pdf', pagesize=A4, rightMargin=18,
        leftMargin=18, topMargin=18, bottomMargin=18)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='align_right', alignment=TA_RIGHT))

    pdf_invoice = PDFInvoice(invoice_no, shop_data, order_data)
    pdf_invoice.generate(styles)

    doc.build(pdf_invoice.body)


if __name__ == '__main__':
    run()
