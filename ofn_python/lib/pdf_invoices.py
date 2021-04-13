import datetime as dt
import io
import os
import requests

from reportlab.platypus import Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch, mm


class InvoiceNo:

    def __init__(self, prev_invoice_no):
        self.prev_invoice_no = prev_invoice_no

    def get_next_invoice_no(self):
        next_invoice_no = int(self.prev_invoice_no.split('-')[-1])
        next_invoice_no += 1
        next_invoice_no = f'RE-{next_invoice_no:07d}'

        return next_invoice_no


class PDFInvoice:

    server_name = 'https://openfoodnetwork.de'
    headers = {
        'Accept': 'application/json;charset=UTF-8',
        'Content-Type': 'application/json'
    }
    params = (('token', os.environ['OPENFOODNETWORK_API_KEY']),)

    def __init__(self, invoice_no, shop_data, order_data):
        self.body = []
        self.invoice_no = invoice_no
        self.shop_data = shop_data
        self.order_data = order_data
        self.tax_rates = {}
        self.payment_state = ''

    def __add_header(self, styles):
        '''Add header section.'''
        logo_response = requests.get(f'{self.server_name}{self.shop_data["logo"]}').content
        logo = Image(io.BytesIO(logo_response), inch, inch)
        p1 = Paragraph(f'<font size="10">{self.order_data["ship_address"]["firstname"]} {self.order_data["ship_address"]["lastname"]}</font><br/>\
        <font size="10">{self.order_data["ship_address"]["address1"]}</font><br/>\
        <font size="10">{self.order_data["ship_address"]["zipcode"]} {self.order_data["ship_address"]["city"]}</font><br/>', styles["Normal"])
        p2 = Paragraph(f'<font size="8"><b>{self.order_data["distributor_name"]}</b></font><br/>\
        <font size="8">{self.shop_data["address"]["address1"]}</font><br/>\
        <font size="8">{self.shop_data["address"]["zipcode"]} {self.shop_data["address"]["city"]}</font><br/>\
        <font size="8">{self.shop_data["email_address"][::-1]}</font><br/>\
        <font size="8">{self.shop_data["phone"]}</font><br/>\
        <font size="8">St.-Nr. 327 5728 1746</font><br/>', styles["align_right"])

        t = Table([['', logo], [p1, p2]])
        table_style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'RIGHT')])
        t.setStyle(table_style)
        self.body.append(t)

    def __add_dates_and_no(self, styles):
        '''Add invoice dates and invoice no. section'''
        order_date = dt.datetime.strptime(self.order_data["completed_at"],
            '%B %d, %Y').strftime('%d.%m.%Y')
        transaction_date = dt.datetime.strptime(self.order_data["payments"][-1]["updated_at"],
            '%b %d, %Y %H:%M').strftime('%d.%m.%Y')

        p1 = Paragraph(f'<font size="12">RECHNUNG</font>', styles["Normal"])

        if self.order_data["payment_state"] == 'paid':
            self.payment_state = 'ABGESCHLOSSEN'
            p2 = Paragraph(f'<font size="8">Rechnungsdatum: {order_date}</font><br/>\
            <font size="8">Leistungsdatum: {transaction_date}</font><br/>\
            <font size="8">Bestelldatum: {order_date}</font><br/>\
            <font size="8">Rechnungsnummer: {self.invoice_no}</font>', styles["Normal"])
        else:
            self.payment_state = 'NICHT ABGESCHLOSSEN'
            p2 = Paragraph(f'<font size="8">Rechnungsdatum: {order_date}</font><br/>\
            <font size="8">Leistungsdatum entspricht Rechnungsdatum</font><br/>\
            <font size="8">Bestelldatum: {order_date}</font><br/>\
            <font size="8">Rechnungsnummer: {self.invoice_no}</font>', styles["Normal"])

        t = Table([[p1, ''], [p2, '']])
        self.body.append(t)

    def __get_product_data(self, product_name):
        '''Get product details.'''
        url = f"{self.server_name}/api/products/bulk_products?q[name_eq]={product_name}"
        response = requests.get(url, headers=self.headers, params=self.params)
        product_data = response.json()
        return product_data

    def __add_table(self, styles):
        '''Add table with items section.'''
        p1 = Paragraph(f'<font size="8"><b>Artikel</b></font>', styles["Normal"])
        p2 = Paragraph(f'<font size="8"><b>Menge</b></font>', styles["align_right"])
        p3 = Paragraph(f'<font size="8"><b>Stückpreis (inkl. Steuern)</b></font>', styles["align_right"])
        p4 = Paragraph(f'<font size="8"><b>Gesamptpreis (inkl. Steuern)</b></font>', styles["align_right"])
        p5 = Paragraph(f'<font size="8"><b>Steuersatz</b></font>', styles["align_right"])
        data = [[p1, p2, p3, p4, p5]]

        if dt.datetime.strptime(self.order_data["completed_at"], '%B %d, %Y').year == 2020:
            tax_rate_1 = '16.00'
            tax_rate_2 = '5.00'
            tax_rate_3 = '10.70'
        else:
            tax_rate_1 = '19.00'
            tax_rate_2 = '7.00'
            tax_rate_3 = '10.70'

        for count, i in enumerate(self.order_data['line_items']):
            print(i["variant"]["product_name"])

            if count == 17:
                t = Table(data, colWidths=(89*mm, 25*mm, 25*mm, 25*mm, 25*mm))
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), '#e8e8e8'),
                    ('BOX', (0, 0), (-1, -1), 0.25, '#000000'),
                    ('LINEBELOW', (0, 0), (-1, -2), 0.25, '#000000')
                ]))
                self.body.append(t)

                self.__add_header(styles)
                self.__add_dates_and_no(styles)

                data = [[p1, p2, p3, p4, p5]]

            product_data = self.__get_product_data(i["variant"]["product_name"])

            try:
                product_data = product_data['products'][-1]
            except IndexError:
                product_data = None

            if product_data:
                tax_category_id = product_data['tax_category_id']

                if tax_category_id == 1:
                    tax_rate = tax_rate_1
                elif tax_category_id == 2:
                    tax_rate = tax_rate_2
                elif tax_category_id == 3:
                    tax_rate = tax_rate_3
                else:
                    tax_rate = '0.00'

                total_price = int(i["quantity"]) * float(i["price"])

                if tax_rate != '0.00':
                    amounts = {'tax_amount': total_price * (1 - 1 / (1 + float(tax_rate) / 100.0)),
                        'total_price': total_price}

                    if tax_rate in self.tax_rates.keys():
                        self.tax_rates[tax_rate].append(amounts)
                    else:
                        self.tax_rates[tax_rate] = [amounts]

                cell1 = [Paragraph(f'<font size="8"><b>{i["variant"]["product_name"]}</b> ({i["variant"]["unit_to_display"]})</font>', styles["Normal"]),
                        Paragraph(f'<font size="7"><i>{product_data["master"]["producer_name"]}</i></font>', styles["Normal"])]
                cell2 = Paragraph(f'<font size="8">{i["quantity"]}</font>', styles["align_right"])
                cell3 = Paragraph(f'<font size="8">{round(float(i["price"]), 2):.2f} €</font>', styles["align_right"])
                cell4 = Paragraph(f'<font size="8">{round(total_price, 2):.2f} €</font>', styles["align_right"])
                cell5 = Paragraph(f'<font size="8">{round(float(tax_rate), 2):.2f} %</font>', styles["align_right"])
                data.append([cell1, cell2, cell3, cell4, cell5])

        shipping_tax_rate = tax_rate_1
        shipping1 = float(self.order_data["adjustments"][0]["amount"])
        shipping2 = float(self.order_data["adjustments"][1]["amount"])
        amounts1 = {'tax_amount': shipping1 * (1 - 1 / (1 + float(shipping_tax_rate) / 100.0)),
            'total_price': shipping1}
        amounts2 = {'tax_amount': shipping2 * (1 - 1 / (1 + float(shipping_tax_rate) / 100.0)),
            'total_price': shipping2}

        if shipping_tax_rate in self.tax_rates.keys():
            self.tax_rates[shipping_tax_rate].append(amounts1)
            self.tax_rates[shipping_tax_rate].append(amounts2)
        else:
            self.tax_rates[shipping_tax_rate] = [amounts1]
            self.tax_rates[shipping_tax_rate] = [amounts2]

        f11 = Paragraph(f'<font size="8"><b>{self.order_data["adjustments"][0]["label"]}</b></font>', styles["Normal"])
        f21 = Paragraph(f'', styles["align_right"])
        f31 = Paragraph(f'', styles["align_right"])
        f41 = Paragraph(f'<font size="8">{round(shipping1, 2):.2f} €</font>', styles["align_right"])
        f51 = Paragraph(f'<font size="8">{round(float(shipping_tax_rate), 2):.2f} %</font>', styles["align_right"])
        f12 = Paragraph(f'<font size="8"><b>{self.order_data["adjustments"][1]["label"]}</b></font>', styles["Normal"])
        f22 = Paragraph(f'', styles["align_right"])
        f32 = Paragraph(f'', styles["align_right"])
        f42 = Paragraph(f'<font size="8">{round(shipping2, 2):.2f} €</font>', styles["align_right"])
        f52 = Paragraph(f'<font size="8">{round(float(shipping_tax_rate), 2):.2f} %</font>', styles["align_right"])
        data.append([f11, f21, f31, f41, f51])
        data.append([f12, f22, f32, f42, f52])
        
        t = Table(data, colWidths=(89*mm, 25*mm, 25*mm, 25*mm, 25*mm))
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#e8e8e8'),
            ('BOX', (0, 0), (-1, -1), 0.25, '#000000'),
            ('LINEBELOW', (0, 0), (-1, -2), 0.25, '#000000')
        ]))
        self.body.append(t)

    def __add_total_amounts(self, styles):
        '''Add total amounts section.'''
        p1 = Paragraph(f'', styles["Normal"])
        p2 = Paragraph(f'<font size="10"><b>Gesamt (inkl. Steuern)</b></font>', styles["align_right"])
        p3 = Paragraph(f'<font size="10"><b>{round(float(self.order_data["total"]), 2):.2f} €</b></font>', styles["align_right"])
        data = [[p1, p2, p3]]

        taxes_total_amount = 0.0
        for key, value in self.tax_rates.items():
            tax_total_amount = round(sum([d['tax_amount'] for d in value]), 2)
            total_amount_without_tax = sum([d['total_price'] for d in value]) - tax_total_amount
            p1 = Paragraph(f'', styles["Normal"])
            p2 = Paragraph(f'<font size="8">Steuersumme ({round(float(key), 2):.2f} %) von {round(total_amount_without_tax, 2):.2f} €</font>', styles["align_right"])
            p3 = Paragraph(f'<font size="8">{round(float(tax_total_amount), 2):.2f} €</font>', styles["align_right"])
            data.append([p1, p2, p3])
            taxes_total_amount += tax_total_amount

        p1 = Paragraph(f'', styles["Normal"])
        p2 = Paragraph(f'<font size="8">Summe (zzgl. Steuern)</font>', styles["align_right"])
        p3 = Paragraph(f'<font size="8">{round(float(self.order_data["total"]) - taxes_total_amount, 2):.2f} €</font>', styles["align_right"])
        data.append([p1, p2, p3])

        t = Table(data)
        self.body.append(t)
        self.body.append(Spacer(1, 24))

    def __add_footer(self, styles):
        '''Add footer section.'''
        p1 = Paragraph(f'<font size="8"><b>Zahlungsübersicht</b></font><br/>', styles["Normal"])
        p2 = Paragraph(f'<font size="8">{self.payment_state}</font><br/>', styles["align_right"])
        t = Table([[p1, p2]])
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), '#b7ddf7')]))
        self.body.append(t)
        self.body.append(Spacer(1, 6))

        p11 = Paragraph(f'<font size="8"><b>DATUM/UHRZEIT</b></font>', styles["Normal"])
        p21 = Paragraph(f'<font size="8"><b>ZAHLUNGSART</b></font>', styles["align_right"])
        p31 = Paragraph(f'<font size="8"><b>ZAHLUNGSSTATUS</b></font>', styles["align_right"])
        p41 = Paragraph(f'<font size="8"><b>BETRAG</b></font>', styles["align_right"])

        p12 = Paragraph(f'<font size="8">{self.order_data["payments"][-1]["updated_at"]}</font>', styles["Normal"])
        p22 = Paragraph(f'<font size="8">{self.order_data["payments"][-1]["payment_method"]}</font>', styles["align_right"])
        p32 = Paragraph(f'<font size="8">{self.payment_state}</font>', styles["align_right"])
        p42 = Paragraph(f'<font size="8">{round(float(self.order_data["payments"][-1]["amount"]), 2):.2f} €</font>', styles["align_right"])

        t = Table([[p11, p21, p31, p41], [p12, p22, p32, p42]])
        t.setStyle(TableStyle([
            ('INNERGRID', (0, 0), (-1, -1), 0.25, '#000000'),
            ('BOX', (0, 0), (-1, -1), 0.25, '#000000')
        ]))
        self.body.append(t)

    def __add_bank_info(self, styles):
        '''Add bank informayion section.'''
        p1 = Paragraph(f'<font size="6"><b>Sparkasse Münsterland Ost</b></font><br/>\
            <font size="6"><b>IBAN DE30 4005 0150 0034 4700 21</b></font><br/>\
            <font size="6"><b>BIC WELADED1MST</b></font><br/>', styles["Normal"])
        self.body.append(Spacer(1, 120))
        self.body.append(p1)

    def generate(self, styles):
        '''General method.'''
        self.__add_header(styles)
        self.__add_dates_and_no(styles)
        self.__add_table(styles)
        self.__add_total_amounts(styles)
        self.__add_footer(styles)
        self.__add_bank_info(styles)
