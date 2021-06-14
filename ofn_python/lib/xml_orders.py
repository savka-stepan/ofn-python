import datetime as dt
import ftplib
import io
import os
import re
from reportlab.platypus import Paragraph

from ofn_python.lib.common.core import OFNData
from ofn_python.lib.common.core_functions import send_email
from ofn_python.xml_templates.xml_template import (
    get_xml_header,
    get_xml_body,
    get_xml_footer,
)


class XMLOrder(OFNData):
    def __init__(self, server_name, headers, params):
        super().__init__(server_name, headers, params)
        self.xml_str = ""
        self.header_correction = {}

    def get_order_header_correction(self):
        """Make order header correction."""
        correction = {}
        correction["completed_at"] = dt.datetime.strptime(
            self.order_data["completed_at"], "%B %d, %Y"
        ).strftime("%Y-%m-%dT%H:%M:%S")

        if "Boxenstopp Albachten" in self.order_data["shipping_method"]["name"]:
            correction[
                "transport_location"
            ] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, Hofladen Freitag, Sendener Stiege 32, 48163 Münster"
            correction["delivery_street"] = "Sendener Stiege 32"
            correction["delivery_zip"] = "48163"
            correction["delivery_city"] = "Münster"
        elif (
            "Boxenstopp Markant Tankstelle Schmidt"
            in self.order_data["shipping_method"]["name"]
        ):
            correction[
                "transport_location"
            ] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, Markant Tankstelle Schmidt, Harkortstr.4, 48163 Münster"
            correction["delivery_street"] = "Harkortstr.4"
            correction["delivery_zip"] = "48163"
            correction["delivery_city"] = "Münster"
        elif (
            "Boxenstopp Innenstadt/Alter Steinweg"
            in self.order_data["shipping_method"]["name"]
        ):
            correction[
                "transport_location"
            ] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, Auenhof Laden, Alter Steinweg 39, 48143 Münster"
            correction["delivery_street"] = "Alter Steinweg 39"
            correction["delivery_zip"] = "48143"
            correction["delivery_city"] = "Münster"
        elif "Boxenstopp Roxel" in self.order_data["shipping_method"]["name"]:
            correction[
                "transport_location"
            ] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, Lager, Im Derdel 18, 48161 Münster"
            correction["delivery_street"] = "Im Derdel 18"
            correction["delivery_zip"] = "48161"
            correction["delivery_city"] = "Münster"
        elif (
            "Boxenstopp Schiffahrter Damm" in self.order_data["shipping_method"]["name"]
        ):
            correction[
                "transport_location"
            ] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, IBS Laden, Schiffahrter Damm 24, 48145 Münster"
            correction["delivery_street"] = "Schiffahrter Damm 24"
            correction["delivery_zip"] = "48145"
            correction["delivery_city"] = "Münster"
        elif (
            "Boxenstopp Wolbecker Str./ Fleischerei Hidding"
            in self.order_data["shipping_method"]["name"]
        ):
            correction[
                "transport_location"
            ] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, Fleischerei Hidding, Wolbecker Str. 222, 48155 Münster"
            correction["delivery_street"] = "Wolbecker Str. 222"
            correction["delivery_zip"] = "48155"
            correction["delivery_city"] = "Münster"
        elif (
            "Abholung in der Bäckerei Schmitz"
            in self.order_data["shipping_method"]["name"]
        ):
            correction[
                "transport_location"
            ] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, Magnusplatz 23, 48351 Everswinkel"
            correction["delivery_street"] = "Magnusplatz 23"
            correction["delivery_zip"] = "48351"
            correction["delivery_city"] = "Everswinkel"
        elif (
            "Abholung in der Fleischerei Lechtermann"
            in self.order_data["shipping_method"]["name"]
        ):
            correction[
                "transport_location"
            ] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, Albersloher Str. 4, 48317 Drensteinfurt"
            correction["delivery_street"] = "Albersloher Str. 4"
            correction["delivery_zip"] = "48317"
            correction["delivery_city"] = "Drensteinfurt"
        else:
            correction[
                "transport_location"
            ] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, {self.order_data['ship_address']['address1']}, {self.order_data['ship_address']['zipcode']} {self.order_data['ship_address']['city']}"
            correction[
                "delivery_street"
            ] = f"{self.order_data['ship_address']['address1']}"
            correction["delivery_zip"] = f"{self.order_data['ship_address']['zipcode']}"
            correction["delivery_city"] = f"{self.order_data['ship_address']['city']}"

        # Order comment
        if self.order_data["special_instructions"]:
            correction["remarks"] = self.order_data["special_instructions"]
        else:
            correction["remarks"] = ""

        self.header_correction = correction

    def add_xml_header(self):
        self.xml_str = get_xml_header(self.order_data, self.header_correction)

    def __get_product_details(self, item, producers_ids, pdf_orders, styles):
        """Make order item correction."""
        correction = {}
        product_name = item["variant"]["product_name"]
        sku = item["variant"]["sku"]

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
            product = self.product_data["products"][0]
        except IndexError:
            product = None

        if product:
            manufacturer_idref = product["producer_id"]
            manufacturer_pid = product["master"]["producer_name"].strip()
            tax_category_id = product["tax_category_id"]

            # --- Special producers pdf generation
            for pdf_order in pdf_orders:
                if pdf_order.supplier_id == product["producer_id"]:
                    print(
                        manufacturer_pid,
                        item["variant"]["product_name"],
                        item["quantity"],
                        item["price"],
                    )
                    p1 = Paragraph(
                        f'<font size="8">{item["variant"]["product_name"]} {item["variant"]["unit_to_display"]}</font>',
                        styles["Normal"],
                    )
                    p2 = Paragraph(
                        f'<font size="8">{item["variant"]["sku"]}</font>',
                        styles["align_right"],
                    )
                    p3 = Paragraph(
                        f'<font size="8">{item["quantity"]}</font>',
                        styles["align_right"],
                    )
                    p4 = Paragraph(
                        f'<font size="8">{item["price"]}</font>',
                        styles["align_right"],
                    )
                    pdf_order.data.append([p1, p2, p3, p4])
                    pdf_order.supplier_name = manufacturer_pid
            # --- Special producers pdf generation

        else:
            tax_category_id = 2
            manufacturer_idref = ""
            manufacturer_pid = ""

        if tax_category_id == 1:
            tax_category = "MwSt.-19"
            tax_rate = "19.00"
        elif tax_category_id == 2:
            tax_category = "MwSt.-7"
            tax_rate = "7.00"
        elif tax_category_id == 3:
            tax_category = "MwSt.-10"
            tax_rate = "10.70"
        else:
            tax_category = "MwSt.-"
            tax_rate = "0.00"

        correction["manufacturer_idref"] = manufacturer_idref
        correction["manufacturer_pid"] = manufacturer_pid
        correction["tax_category"] = tax_category
        correction["tax_rate"] = tax_rate

        # Fix product display name
        if item["variant"]["product_name"] == item["variant"]["name_to_display"]:
            correction[
                "description_short"
            ] = f"{item['variant']['product_name']} {item['variant']['unit_to_display']}"
        else:
            correction[
                "description_short"
            ] = f"{item['variant']['product_name']} {item['variant']['name_to_display']} {item['variant']['unit_to_display']}"

        return correction

    def add_xml_body(self, producers_ids, pdf_orders, styles):
        """Iterate through products."""
        print("Products:")
        skus_wrong_format = []
        for count, item in enumerate(self.order_data["line_items"], 1):
            print(item["variant"]["sku"])
            correction = self.__get_product_details(item, producers_ids, pdf_orders, styles)

            # Get all skus with wrong format
            if not re.match(r"\b\w{3}\-\w{3}\-\d{3,}\b", item["variant"]["sku"]):
                skus_wrong_format.append(
                    {
                        "sku": item["variant"]["sku"],
                        "producer": correction["manufacturer_pid"],
                    }
                )

            self.xml_str += get_xml_body(item, count, self.order_data, correction)

        return skus_wrong_format

    def add_xml_footer(self):
        self.xml_str += get_xml_footer(self.order_data)

    def replace_special_chr(self, ch1, ch2):
        """Replace char1 with char2."""
        if ch1 in self.xml_str:
            self.xml_str = self.xml_str.replace(ch1, ch2)

    def send_email_wrong_sku_format(self, skus_wrong_format):
        """Send email with wrong sku format."""
        receivers = [
            os.environ.get("EMAIL_OFN"),
        ]
        subject = "SKU Fehler in Bauernbox"
        body = "Es gab ein paar Fehler mit:"
        for sku_wrong_format in skus_wrong_format:
            body += f"<br>SKU {sku_wrong_format['sku']}, von Produzent {sku_wrong_format['producer']}"
        body += "<br>bitte prüfen."
        send_email(receivers, subject, body)

    def send_email_zip_not_in_range(self, order_no, delivery_zip):
        """Send email if zipcode not in certain range."""
        receivers = [
            os.environ.get("EMAIL_OFN"),
        ]
        subject = "Falsche Postleitzahl in Bauernbox"
        body = f"Bestellnummer {order_no}, Postleitzahl {delivery_zip}<br>bitte prüfen."
        send_email(receivers, subject, body)

    def send_by_email(self, filename, attchmnt):
        """Send xml file by email."""
        receivers = [
            os.environ.get("EMAIL_OPENTRANSORDERS"),
        ]
        subject = "Opentransorders"
        body = "Opentransorders xml files:"
        send_email(receivers, subject, body, filename=filename, attchmnt=attchmnt)

    def send_to_ftp_server(self, filename, attchmnt):
        """Send xml file to ftp server."""
        with ftplib.FTP(
            os.environ.get("FTP_SERVER"),
            os.environ.get("FTP_USERNAME"),
            os.environ.get("FTP_PASSWORD"),
        ) as ftp:
            ftp.storbinary(f"STOR orders/{filename}", io.BytesIO(attchmnt))

    def save_to_local_storage(self, tree, filename):
        """Save to local storage."""
        tree.write(
            filename, encoding="utf-8", xml_declaration=True, short_empty_elements=False
        )
