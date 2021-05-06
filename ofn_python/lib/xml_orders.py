import datetime as dt
import ftplib
import io
import os
import re

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

    def __make_order_item_correction(self, item, eans):
        """Make order item correction."""
        correction = {}
        self.get_product_data(item["variant"]["product_name"])

        try:
            product = self.product_data["products"][0]
        except IndexError:
            product = None

        if product:
            # Get manufacturer
            correction["manufacturer_idref"] = product["producer_id"]
            correction["manufacturer_pid"] = product["master"]["producer_name"]

            # Get tax
            tax_category_id = product["tax_category_id"]

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

            correction["tax_category"] = tax_category
            correction["tax_rate"] = tax_rate

        else:
            # Get manufacturer
            correction["manufacturer_idref"] = ""
            correction["manufacturer_pid"] = ""
            # Get tax
            correction["tax_category"] = "MwSt.-"
            correction["tax_rate"] = "0.00"

        # Get EAN from google sheet
        found_sku = eans.loc[eans["sku"] == item["variant"]["sku"]]
        if not found_sku.empty:
            found_ean = found_sku.iloc[0]["EAN"]
            if found_ean == "":
                correction["ean"] = item["variant"]["sku"]
            else:
                correction["ean"] = found_ean
        else:
            correction["ean"] = item["variant"]["sku"]

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

    def add_xml_body(self, eans):
        """Iterate through products."""
        print("Products:")
        skus_wrong_format = []
        for count, item in enumerate(self.order_data["line_items"], 1):
            print(item["variant"]["sku"])
            correction = self.__make_order_item_correction(item, eans)

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
            os.environ["EMAIL_OFN"],
        ]
        subject = "SKU Fehler in Bauernbox"
        body = "Es gab ein paar Fehler mit:"
        for sku_wrong_format in skus_wrong_format:
            body += f"<br>SKU {sku_wrong_format['sku']}, von Produzent {sku_wrong_format['producer']}"
        body += "<br>bitte prüfen."
        send_email(receivers, subject, body, None, None)

    def send_email_zip_not_in_range(self, order_no, delivery_zip):
        """Send email if zipcode not in certain range."""
        receivers = [
            os.environ["EMAIL_OFN"],
        ]
        subject = "Falsche Postleitzahl in Bauernbox"
        body = f"Bestellnummer {order_no}, Postleitzahl {delivery_zip}<br>bitte prüfen."
        send_email(receivers, subject, body, None, None)

    def send_by_email(self, filename, attchmnt):
        """Send xml file by email."""
        receivers = [
            os.environ["EMAIL_OPENTRANSORDERS"],
        ]
        subject = "Opentransorders"
        body = "Opentransorders xml files:"
        send_email(receivers, subject, body, filename, attchmnt)

    def send_to_ftp_server(self, filename, attchmnt):
        """Send xml file to ftp server."""
        with ftplib.FTP(
            os.environ["FTP_SERVER"],
            os.environ["FTP_USERNAME"],
            os.environ["FTP_PASSWORD"],
        ) as ftp:
            ftp.storbinary(f"STOR orders/{filename}", io.BytesIO(attchmnt))

    def save_to_local_storage(self, tree, filename):
        """Save to local storage."""
        tree.write(
            filename, encoding="utf-8", xml_declaration=True, short_empty_elements=False
        )
