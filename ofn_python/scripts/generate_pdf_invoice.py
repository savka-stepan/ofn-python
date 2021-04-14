import datetime as dt
import ftplib
import io
import os
import requests

from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate

from ofn_python.lib.common.core_functions import get_data_from_google_sheet
from ofn_python.lib.pdf_invoices import InvoiceNo, PDFInvoice


def add_bank_info(canvas, doc):
    p1 = 'Sparkasse Münsterland Ost'
    p2 = 'IBAN DE30 4005 0150 0034 4700 21'
    p3 = 'BIC WELADED1MST'
    canvas.setFont("Helvetica-Bold", 6)
    canvas.drawString(11*mm, 11*mm, p1)
    canvas.drawString(11*mm, 8*mm, p2)
    canvas.drawString(11*mm, 5*mm, p3)

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

    sheet_df, sheet = get_data_from_google_sheet('Bauernbox Übersicht', ['number', 'invoice_no'])
    worksheet = sheet.worksheet('münster')

    last_invoice = list(filter(None, sheet_df['invoice_no'].tolist()))
    if last_invoice:
        last_invoice = last_invoice[-1]
    else:
        last_invoice = 'RE-0000000'

    cell_rows = []
    new_data = []
    sheet_df = sheet_df.loc[sheet_df['invoice_no'] == '']
    for i in sheet_df['number'].tolist():
        last_invoice_no = InvoiceNo(last_invoice)
        invoice_no = last_invoice_no.get_next_invoice_no()
        last_invoice = invoice_no

        order_url = f'{server_name}/api/orders/{i}'
        response = requests.get(order_url, headers=headers, params=params)
        order_data = response.json()

        stream = io.BytesIO()
        doc = SimpleDocTemplate(stream, pagesize=A4, rightMargin=18, leftMargin=18, topMargin=18,
            bottomMargin=18)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='align_right', alignment=TA_RIGHT))

        print(i, invoice_no)
        
        pdf_invoice = PDFInvoice(invoice_no, shop_data, order_data)
        pdf_invoice.generate(styles)

        doc.build(pdf_invoice.body, onFirstPage=add_bank_info, onLaterPages=add_bank_info)
        result = stream.getvalue()
        stream.close()

        with ftplib.FTP(os.environ['FTP_SERVER'], os.environ['FTP_USERNAME'],
                os.environ['FTP_PASSWORD']) as ftp:
            ftp.storbinary(f'STOR invoices/invoice{invoice_no}.pdf', io.BytesIO(result))

        cell_rows.append(worksheet.find(i).row)
        new_data.append([invoice_no, dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')])

        print('---')

    # Update sheet with new data
    sheet.values_update(
        f'münster!AA{cell_rows[0]}:AB{cell_rows[-1]}', 
        params={'valueInputOption': 'RAW'}, 
        body={'values': new_data}
    )


if __name__ == '__main__':
    run()
