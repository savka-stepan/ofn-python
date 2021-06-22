import datetime as dt
import io
import os
import requests

from reportlab.platypus import Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch, mm

from ofn_python.lib.common.core import OFNData
from ofn_python.lib.common.core_functions import send_email


class InvoiceNo:
    def __init__(self, prev_invoice_no):
        self.prev_invoice_no = prev_invoice_no

    def get_next_invoice_no(self):
        next_invoice_no = int(self.prev_invoice_no.split("-")[-1])
        next_invoice_no += 1
        next_invoice_no = f"RE-{next_invoice_no:07d}"

        return next_invoice_no


class PDFInvoice(OFNData):
    def __init__(self, server_name, headers, params):
        super().__init__(server_name, headers, params)
        self.body = []
        self.tax_rates = {}
        self.payment_state = ""

    def add_header(self, shop_data, styles):
        """Add header section."""
        logo_response = requests.get(f'{self.server_name}{shop_data["logo"]}').content
        logo = Image(io.BytesIO(logo_response), inch, inch)
        p1 = Paragraph(
            f'<font size="10">{self.order_data["ship_address"]["firstname"]} {self.order_data["ship_address"]["lastname"]}</font><br/>\
        <font size="10">{self.order_data["ship_address"]["address1"]}</font><br/>\
        <font size="10">{self.order_data["ship_address"]["zipcode"]} {self.order_data["ship_address"]["city"]}</font><br/>',
            styles["Normal"],
        )
        p2 = Paragraph(
            f'<font size="8"><b>{self.order_data["distributor_name"]}</b></font><br/>\
        <font size="8">{shop_data["address"]["address1"]}</font><br/>\
        <font size="8">{shop_data["address"]["zipcode"]} {shop_data["address"]["city"]}</font><br/>\
        <font size="8">{shop_data["email_address"][::-1]}</font><br/>\
        <font size="8">{shop_data["phone"]}</font><br/>\
        <font size="8">St.-Nr. 336/5802/6337</font><br/>',
            styles["align_right"],
        )

        t = Table([["", logo], [p1, p2]])
        table_style = TableStyle([("ALIGN", (0, 0), (-1, -1), "RIGHT")])
        t.setStyle(table_style)
        self.body.append(t)

    def add_dates_and_no(self, invoice_no, styles):
        """Add invoice dates and invoice no. section"""
        order_date = dt.datetime.strptime(
            self.order_data["completed_at"], "%B %d, %Y"
        ).strftime("%d.%m.%Y")
        transaction_date = dt.datetime.strptime(
            self.order_data["payments"][-1]["updated_at"], "%b %d, %Y %H:%M"
        ).strftime("%d.%m.%Y")

        p1 = Paragraph(f'<font size="12">RECHNUNG</font>', styles["Normal"])

        if self.order_data["payment_state"] == "paid":
            self.payment_state = "ABGESCHLOSSEN"
            p2 = Paragraph(
                f'<font size="8">Rechnungsdatum: {order_date}</font><br/>\
            <font size="8">Leistungsdatum: {transaction_date}</font><br/>\
            <font size="8">Bestelldatum: {order_date}</font><br/>\
            <font size="8">Bestellnummer: {self.order_data["number"]}</font><br/>\
            <font size="8">Rechnungsnummer: {invoice_no}</font>',
                styles["Normal"],
            )
        else:
            self.payment_state = "NICHT ABGESCHLOSSEN"
            p2 = Paragraph(
                f'<font size="8">Rechnungsdatum: {order_date}</font><br/>\
            <font size="8">Leistungsdatum entspricht Rechnungsdatum</font><br/>\
            <font size="8">Bestelldatum: {order_date}</font><br/>\
            <font size="8">Bestellnummer: {self.order_data["number"]}</font><br/>\
            <font size="8">Rechnungsnummer: {invoice_no}</font>',
                styles["Normal"],
            )

        t = Table([[p1, ""], [p2, ""]])
        self.body.append(t)

    def add_table(self, shop_data, invoice_no, producers_ids, styles):
        """Add table with items section."""
        p1 = Paragraph(f'<font size="8"><b>Artikel</b></font>', styles["Normal"])
        p2 = Paragraph(f'<font size="8"><b>Menge</b></font>', styles["align_right"])
        p3 = Paragraph(
            f'<font size="8"><b>Stückpreis (inkl. Steuern)</b></font>',
            styles["align_right"],
        )
        p4 = Paragraph(
            f'<font size="8"><b>Gesamptpreis (inkl. Steuern)</b></font>',
            styles["align_right"],
        )
        p5 = Paragraph(
            f'<font size="8"><b>Steuersatz</b></font>', styles["align_right"]
        )
        data = [[p1, p2, p3, p4, p5]]

        if (
            dt.datetime.strptime(self.order_data["completed_at"], "%B %d, %Y").year
            == 2020
        ):
            tax_rate_1 = "16.00"
            tax_rate_2 = "5.00"
            tax_rate_3 = "10.70"
        else:
            tax_rate_1 = "19.00"
            tax_rate_2 = "7.00"
            tax_rate_3 = "10.70"

        items_count = 0
        # not_found_products = []
        for count, i in enumerate(self.order_data["line_items"]):
            product_name = i["variant"]["product_name"]
            sku = i["variant"]["sku"]
            quantity = i["quantity"]
            price = i["price"]
            print(product_name, quantity, price)
            items_count = count

            if count % 17 == 0 and count > 0:
                t = Table(data, colWidths=(89 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm))
                t.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), "#e8e8e8"),
                            ("BOX", (0, 0), (-1, -1), 0.25, "#000000"),
                            ("LINEBELOW", (0, 0), (-1, -2), 0.25, "#000000"),
                        ]
                    )
                )
                self.body.append(t)

                self.add_header(shop_data, styles)
                self.add_dates_and_no(invoice_no, styles)

                data = [[p1, p2, p3, p4, p5]]

            if product_name == "Feldsalat ":
                self.get_product_data_cont(product_name)

                if len(self.product_data["products"]) > 1:
                    variant_data = self.get_variants_by_sku(sku)

                    for vd in variant_data:
                        self.get_product_data_by_variant_id(vd["id"])

                        if self.product_data["products"]:
                            break

            else:
                self.get_product_data(product_name)

            if not self.product_data["products"]:
                self.get_product_data_cont(product_name)

                if len(self.product_data["products"]) > 1:
                    variant_data = self.get_variants_by_sku(sku)

                    for vd in variant_data:
                        self.get_product_data_by_variant_id(vd["id"])

                        if self.product_data["products"]:
                            break

            if len(self.product_data["products"]) > 1:
                self.product_data["products"] = [
                    i
                    for i in self.product_data["products"]
                    if i["producer_id"] in producers_ids
                ]

            try:
                product_data = self.product_data["products"][0]
            except IndexError:
                product_data = None

            producer_name = ""
            total_price = int(quantity) * float(price)
            tax_rate = "0.00"

            if product_data:
                tax_category_id = product_data["tax_category_id"]
                producer_name = product_data["master"]["producer_name"]
            else:
                tax_category_id = 2
                # not_found_products.append(product_name)

            print(f"Tax category {tax_category_id}, Producer name {producer_name}")

            if tax_category_id == 1:
                tax_rate = tax_rate_1
            elif tax_category_id == 2:
                tax_rate = tax_rate_2
            elif tax_category_id == 3:
                tax_rate = tax_rate_3
            else:
                tax_rate = "0.00"

            if tax_rate != "0.00":
                amounts = {
                    "tax_amount": total_price * (1 - 1 / (1 + float(tax_rate) / 100.0)),
                    "total_price": total_price,
                }

                if tax_rate in self.tax_rates.keys():
                    self.tax_rates[tax_rate].append(amounts)
                else:
                    self.tax_rates[tax_rate] = [amounts]

            cell1 = [
                Paragraph(
                    f'<font size="8"><b>{product_name}</b> {i["variant"]["unit_to_display"]}</font>',
                    styles["Normal"],
                ),
                Paragraph(
                    f'<font size="7"><i>{producer_name}</i></font>', styles["Normal"]
                ),
            ]
            cell2 = Paragraph(
                f'<font size="8">{quantity}</font>', styles["align_right"]
            )
            cell3 = Paragraph(
                f'<font size="8">{round(float(price), 2):.2f} €</font>',
                styles["align_right"],
            )
            cell4 = Paragraph(
                f'<font size="8">{round(total_price, 2):.2f} €</font>',
                styles["align_right"],
            )
            cell5 = Paragraph(
                f'<font size="8">{round(float(tax_rate), 2):.2f} %</font>',
                styles["align_right"],
            )
            data.append([cell1, cell2, cell3, cell4, cell5])

        # if not_found_products:
        #     send_email(
        #         ["it@bauernbox.com", "savka.stepan.92@gmail.com"],
        #         "Couldn't find product",
        #         f'Order {self.order_data["number"]} products: {not_found_products}'
        #     )

        shipping_tax_rate = tax_rate_1
        for adjustment in self.order_data["adjustments"]:
            if adjustment["originator_type"] == "Spree::ShippingMethod":
                shipping_amount = float(adjustment["amount"])
                shipping_amounts = {
                    "tax_amount": shipping_amount
                    * (1 - 1 / (1 + float(shipping_tax_rate) / 100.0)),
                    "total_price": shipping_amount,
                }

                if shipping_tax_rate in self.tax_rates.keys():
                    self.tax_rates[shipping_tax_rate].append(shipping_amounts)
                else:
                    self.tax_rates[shipping_tax_rate] = [shipping_amounts]

                f11 = Paragraph(
                    f'<font size="8"><b>{adjustment["label"]}</b></font>',
                    styles["Normal"],
                )
                f21 = Paragraph(f"", styles["align_right"])
                f31 = Paragraph(f"", styles["align_right"])
                f41 = Paragraph(
                    f'<font size="8">{round(shipping_amount, 2):.2f} €</font>',
                    styles["align_right"],
                )
                f51 = Paragraph(
                    f'<font size="8">{round(float(shipping_tax_rate), 2):.2f} %</font>',
                    styles["align_right"],
                )
                data.append([f11, f21, f31, f41, f51])

        t = Table(data, colWidths=(89 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm))
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), "#e8e8e8"),
                    ("BOX", (0, 0), (-1, -1), 0.25, "#000000"),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.25, "#000000"),
                ]
            )
        )
        self.body.append(t)

        return items_count

    def add_total_amounts(self, styles):
        """Add total amounts section."""
        p1 = Paragraph(f"", styles["Normal"])
        p2 = Paragraph(
            f'<font size="10"><b>Gesamt (inkl. Steuern)</b></font>',
            styles["align_right"],
        )
        p3 = Paragraph(
            f'<font size="10"><b>{round(float(self.order_data["total"]), 2):.2f} €</b></font>',
            styles["align_right"],
        )
        data = [[p1, p2, p3]]

        taxes_total_amount = 0.0
        tax_amount_5 = 0.0
        tax_amount_7 = 0.0
        tax_amount_10 = 0.0
        tax_amount_16 = 0.0
        tax_amount_19 = 0.0
        net_amount_5 = 0.0
        net_amount_7 = 0.0
        net_amount_10 = 0.0
        net_amount_16 = 0.0
        net_amount_19 = 0.0
        for key, value in self.tax_rates.items():
            tax_total_amount = round(sum([d["tax_amount"] for d in value]), 2)
            total_amount_without_tax = round(
                sum([d["total_price"] for d in value]) - tax_total_amount, 2
            )
            p1 = Paragraph(f"", styles["Normal"])
            p2 = Paragraph(
                f'<font size="8">Steuersumme ({round(float(key), 2):.2f} %) von {round(total_amount_without_tax, 2):.2f} €</font>',
                styles["align_right"],
            )
            p3 = Paragraph(
                f'<font size="8">{round(float(tax_total_amount), 2):.2f} €</font>',
                styles["align_right"],
            )
            data.append([p1, p2, p3])
            taxes_total_amount += tax_total_amount

            if key == "5.00":
                tax_amount_5 = tax_total_amount
                net_amount_5 = total_amount_without_tax
            if key == "7.00":
                tax_amount_7 = tax_total_amount
                net_amount_7 = total_amount_without_tax
            if key == "10.70":
                tax_amount_10 = tax_total_amount
                net_amount_10 = total_amount_without_tax
            if key == "16.00":
                tax_amount_16 = tax_total_amount
                net_amount_16 = total_amount_without_tax
            if key == "19.00":
                tax_amount_19 = tax_total_amount
                net_amount_19 = total_amount_without_tax

        p1 = Paragraph(f"", styles["Normal"])
        p2 = Paragraph(
            f'<font size="8">Summe (zzgl. Steuern)</font>', styles["align_right"]
        )
        p3 = Paragraph(
            f'<font size="8">{round(float(self.order_data["total"]) - taxes_total_amount, 2):.2f} €</font>',
            styles["align_right"],
        )
        data.append([p1, p2, p3])

        taxes_total_amount = round(taxes_total_amount, 2)

        t = Table(data)
        self.body.append(t)
        self.body.append(Spacer(1, 24))

        return (
            (tax_amount_5, net_amount_5),
            (tax_amount_7, net_amount_7),
            (tax_amount_10, net_amount_10),
            (tax_amount_16, net_amount_16),
            (tax_amount_19, net_amount_19),
            taxes_total_amount,
        )

    def add_footer(self, styles):
        """Add footer section."""
        p1 = Paragraph(
            f'<font size="8"><b>Zahlungsübersicht</b></font><br/>', styles["Normal"]
        )
        p2 = Paragraph(
            f'<font size="8">{self.payment_state}</font><br/>', styles["align_right"]
        )
        t = Table([[p1, p2]])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), "#b7ddf7")]))
        self.body.append(t)
        self.body.append(Spacer(1, 6))

        p11 = Paragraph(f'<font size="8"><b>DATUM/UHRZEIT</b></font>', styles["Normal"])
        p21 = Paragraph(
            f'<font size="8"><b>ZAHLUNGSART</b></font>', styles["align_right"]
        )
        p31 = Paragraph(
            f'<font size="8"><b>ZAHLUNGSSTATUS</b></font>', styles["align_right"]
        )
        p41 = Paragraph(f'<font size="8"><b>BETRAG</b></font>', styles["align_right"])

        p12 = Paragraph(
            f'<font size="8">{self.order_data["payments"][-1]["updated_at"]}</font>',
            styles["Normal"],
        )
        p22 = Paragraph(
            f'<font size="8">{self.order_data["payments"][-1]["payment_method"]}</font>',
            styles["align_right"],
        )
        p32 = Paragraph(
            f'<font size="8">{self.payment_state}</font>', styles["align_right"]
        )
        p42 = Paragraph(
            f'<font size="8">{round(float(self.order_data["payments"][-1]["amount"]), 2):.2f} €</font>',
            styles["align_right"],
        )

        t = Table([[p11, p21, p31, p41], [p12, p22, p32, p42]])
        t.setStyle(
            TableStyle(
                [
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, "#000000"),
                    ("BOX", (0, 0), (-1, -1), 0.25, "#000000"),
                ]
            )
        )
        self.body.append(t)
