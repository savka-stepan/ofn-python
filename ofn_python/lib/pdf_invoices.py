import datetime as dt
import io
import requests

from reportlab.platypus import Paragraph, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class InvoiceNo:

    def __init__(self, prev_invoice_no):
        self.prev_invoice_no = prev_invoice_no

    def get_next_invoice_no(self):
        next_invoice_no = int(self.prev_invoice_no.split('-')[-1])
        next_invoice_no += 1
        next_invoice_no = f'RE-{next_invoice_no:07d}'

        return next_invoice_no


class PDFInvoice:

    def __init__(self, invoice_no, shop_data, order_data):
        self.body = []
        self.invoice_no = invoice_no
        self.shop_data = shop_data
        self.order_data = order_data

    def __add_header(self, styles):
        logo_response = requests.get(f'https://openfoodnetwork.de{self.shop_data["logo"]}').content
        logo = Image(io.BytesIO(logo_response), inch, inch)
        p1 = f'<font size="10">{self.order_data["ship_address"]["firstname"]} {self.order_data["ship_address"]["lastname"]}</font><br/>\
        <font size="10">{self.order_data["ship_address"]["address1"]}</font><br/>\
        <font size="10">{self.order_data["ship_address"]["zipcode"]} {self.order_data["ship_address"]["city"]}</font><br/>'
        p2 = f'<font size="8"><b>{self.order_data["distributor_name"]}</b></font><br/>\
        <font size="8">{self.shop_data["address"]["address1"]}</font><br/>\
        <font size="8">{self.shop_data["address"]["zipcode"]} {self.shop_data["address"]["city"]}</font><br/>\
        <font size="8">{self.shop_data["email_address"][::-1]}</font><br/>\
        <font size="8">{self.shop_data["phone"]}</font><br/>\
        <font size="8">St.-Nr. 327 5728 1746</font><br/>'

        data = [['', logo],
                [Paragraph(p1, styles["Normal"]), Paragraph(p2, styles["align_right"])]]
        t = Table(data)
        table_style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'RIGHT')])
        t.setStyle(table_style)
        self.body.append(t)

    def __add_dates_and_no(self, styles):
        order_date = dt.datetime.strptime(self.order_data["completed_at"],
            '%B %d, %Y').strftime('%d.%m.%Y')
        transaction_date = dt.datetime.strptime(self.order_data["payments"][-1]["updated_at"],
            '%b %d, %Y %H:%M').strftime('%d.%m.%Y')

        p1 = f'<font size="12">RECHNUNG</font>'

        if self.order_data["payment_state"] == 'paid':
            payment_state = 'ABGESCHLOSSEN'
            p2 = f'<font size="8">Rechnungsdatum: {order_date}</font><br/>\
            <font size="8">Leistungsdatum: {transaction_date}</font><br/>\
            <font size="8">Bestelldatum: {order_date}</font><br/>\
            <font size="8">Rechnungsnummer: {self.invoice_no}</font>'
        else:
            payment_state = 'NICHT ABGESCHLOSSEN'
            p2 = f'<font size="8">Rechnungsdatum: {order_date}</font><br/>\
            <font size="8">Leistungsdatum entspricht Rechnungsdatum</font><br/>\
            <font size="8">Bestelldatum: {order_date}</font><br/>\
            <font size="8">Rechnungsnummer: {self.invoice_no}</font>'

        data = [[Paragraph(p1, styles["Normal"]), ''],
                [Paragraph(p2, styles["Normal"]), '']]
        t = Table(data)
        self.body.append(t)

    def __add_table(self, styles):
        p1 = Paragraph(f'<font size="8"><b>Artikel</b></font>', styles["Normal"])
        p2 = Paragraph(f'<font size="8"><b>Menge</b></font>', styles["align_right"])
        p3 = Paragraph(f'<font size="8"><b>Stückpreis (inkl. Steuern)</b></font>', styles["align_right"])
        p4 = Paragraph(f'<font size="8"><b>Gesamptpreis (inkl. Steuern)</b></font>', styles["align_right"])
        p5 = Paragraph(f'<font size="8"><b>Steuersatz</b></font>', styles["align_right"])
        data = [[p1, p2, p3, p4, p5]]

        tax_rates = {}
        for i in order_data['line_items']:
            product_url = f'https://openfoodnetwork.de/api/products/bulk_products?q[name_eq]={i["variant"]["product_name"]}'
            response = requests.get(product_url, headers=headers, params=params)
            product_data = response.json()

            if product_data:
                product_data = product_data["products"][-1]

            tax_category_id = product_data['tax_category_id']

            if tax_category_id == 1:
                tax_rate = '19.00'
            elif tax_category_id == 2:
                tax_rate = '7.00'
            elif tax_category_id == 3:
                tax_rate = '10.70'
            else:
                tax_rate = '0.00'

            total_price = int(i["quantity"]) * float(i["price"])

            if tax_rate != '0.00':
                amounts = {'tax_amount': total_price * float(tax_rate) / 100.0,
                    'total_price': total_price}

                if tax_rate in tax_rates.keys():
                    tax_rates[tax_rate].append(amounts)
                else:
                    tax_rates[tax_rate] = [amounts]

            cell1_text = [Paragraph(f'<font size="8"><b>{i["variant"]["product_name"]}</b> ({i["variant"]["unit_to_display"]})</font>', styles["Normal"]),
            Paragraph(f'<font size="7"><i>{product_data["master"]["producer_name"]}</i></font>', styles["Normal"])]
            cell1 = cell1_text
            cell2 = Paragraph(f'<font size="8">{i["quantity"]}</font>', styles["align_right"])
            cell3 = Paragraph(f'<font size="8">{round(float(i["price"]), 2):.2f} €</font>', styles["align_right"])
            cell4 = Paragraph(f'<font size="8">{round(total_price, 2):.2f} €</font>', styles["align_right"])
            cell5 = Paragraph(f'<font size="8">{round(float(tax_rate), 2):.2f} %</font>', styles["align_right"])
            data.append([cell1, cell2, cell3, cell4, cell5])

        shipping_tax_rate = '19.00'
        shipping_total_price = float(order_data["adjustments"][0]["amount"])
        amounts = {'tax_amount': shipping_total_price * float(shipping_tax_rate) / 100.0,
            'total_price': shipping_total_price}

        if shipping_tax_rate in tax_rates.keys():
            tax_rates[shipping_tax_rate].append(amounts)
        else:
            tax_rates[shipping_tax_rate] = [amounts]

        f11 = Paragraph(f'<font size="8"><b>{order_data["adjustments"][0]["label"]}</b></font>', styles["Normal"])
        f21 = Paragraph(f'', styles["align_right"])
        f31 = Paragraph(f'', styles["align_right"])
        f41 = Paragraph(f'<font size="8">{round(shipping_total_price, 2):.2f} €</font>', styles["align_right"])
        f51 = Paragraph(f'<font size="8">{round(float(shipping_tax_rate), 2):.2f} %</font>', styles["align_right"])
        f12 = Paragraph(f'<font size="8"><b>{order_data["adjustments"][1]["label"]}</b></font>', styles["Normal"])
        f22 = Paragraph(f'', styles["align_right"])
        f32 = Paragraph(f'', styles["align_right"])
        f42 = Paragraph(f'<font size="8">{round(float(order_data["adjustments"][1]["amount"]), 2):.2f} €</font>', styles["align_right"])
        f52 = Paragraph(f'', styles["align_right"])
        data.append([f11, f21, f31, f41, f51])
        data.append([f12, f22, f32, f42, f52])
        
        t = Table(data, colWidths=(89*mm, 25*mm, 25*mm, 25*mm, 25*mm))
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#e8e8e8'),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('LINEBELOW', (0, 0), (-1, -2), 0.25, colors.black)
        ]))
        body.append(t)

    def __add_footer(self):
        pass

    def generate(self, styles):
        self.__add_header(styles)
        self.__add_dates_and_no(styles)
