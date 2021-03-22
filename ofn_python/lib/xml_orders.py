import datetime as dt
import ftplib
import io
import os
import re
import requests
import smtplib
import xml.etree.ElementTree as ET

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ofn_python.lib.common.core_functions import get_data_from_google_sheet
from ofn_python.xml_templates.xml_template import get_xml_header, get_xml_body, get_xml_footer


class XMLOrder:

    server_name = 'https://openfoodnetwork.de'
    headers = {
        'Accept': 'application/json;charset=UTF-8',
        'Content-Type': 'application/json'
    }
    params = (('token', os.environ['OPENFOODNETWORK_API_KEY']),)
    eans = get_data_from_google_sheet('Produktliste_MSB_XXX_Artikelstammdaten', ['sku', 'EAN'])[0]
    postal_codes = ['48143', '48147', '48145', '48157', '48159', '48151', '48155', '48153',
    '48161', '48167', '48165', '48163', '48149']
    
    def __init__(self, order_no):
        self.xml_str = ''
        self.order_data = {}
        self.order_no = order_no

    def __get_order_data(self):
        '''Get order details.'''
        url = f'{self.server_name}/api/orders/{self.order_no}'
        response = requests.get(url, headers=self.headers, params=self.params)
        self.order_data = response.json()

    def __get_order_header_correction(self):
        '''Make order header correction.'''
        correction = {}
        correction['completed_at'] = dt.datetime.strptime(self.order_data['completed_at'],
            '%B %d, %Y').strftime('%Y-%m-%dT%H:%M:%S')

        if 'Boxenstopp Albachten' in self.order_data['shipping_method']['name']:
            correction['transport_location'] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, Hofladen Freitag, Sendener Stiege 32, 48163 Münster"
            correction['delivery_street'] = 'Sendener Stiege 32'
            correction['delivery_zip'] = '48163'
            correction['delivery_city'] = 'Münster'
        elif 'Boxenstopp Harkortstr.4 / Markant Tankstelle' in self.order_data['shipping_method']['name']:
            correction['transport_location'] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, Markant Tankstelle Schmidt, Harkortstr.4, 48163 Münster"
            correction['delivery_street'] = 'Harkortstr.4'
            correction['delivery_zip'] = '48163'
            correction['delivery_city'] = 'Münster'
        elif 'Boxenstopp Innenstadt/Alter Steinweg' in self.order_data['shipping_method']['name']:
            correction['transport_location'] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, Auenhof Laden, Alter Steinweg 39, 48143 Münster"
            correction['delivery_street'] = 'Alter Steinweg 39'
            correction['delivery_zip'] = '48143'
            correction['delivery_city'] = 'Münster'
        elif 'Boxenstopp Roxel' in self.order_data['shipping_method']['name']:
            correction['transport_location'] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, Lager, Im Derdel 18, 48161 Münster"
            correction['delivery_street'] = 'Im Derdel 18'
            correction['delivery_zip'] = '48161'
            correction['delivery_city'] = 'Münster'
        elif 'Boxenstopp Schiffahrter Damm' in self.order_data['shipping_method']['name']:
            correction['transport_location'] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, IBS Laden, Schiffahrter Damm 24, 48145 Münster"
            correction['delivery_street'] = 'Schiffahrter Damm 24'
            correction['delivery_zip'] = '48145'
            correction['delivery_city'] = 'Münster'
        elif 'Abholung in der Bäckerei Schmitz' in self.order_data['shipping_method']['name']:
            correction['transport_location'] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, Magnusplatz 23, 48351 Everswinkel"
            correction['delivery_street'] = 'Magnusplatz 23'
            correction['delivery_zip'] = '48351'
            correction['delivery_city'] = 'Everswinkel'
        elif 'Abholung in der Fleischerei Lechtermann' in self.order_data['shipping_method']['name']:
            correction['transport_location'] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, Albersloher Str. 4, 48317 Drensteinfurt"
            correction['delivery_street'] = 'Albersloher Str. 4'
            correction['delivery_zip'] = '48317'
            correction['delivery_city'] = 'Drensteinfurt'
        else:
            correction['transport_location'] = f"{self.order_data['ship_address']['firstname']} {self.order_data['ship_address']['lastname']}, {self.order_data['ship_address']['address1']}, {self.order_data['ship_address']['zipcode']} {self.order_data['ship_address']['city']}"
            correction['delivery_street'] = f"{self.order_data['ship_address']['address1']}"
            correction['delivery_zip'] = f"{self.order_data['ship_address']['zipcode']}"
            correction['delivery_city'] = f"{self.order_data['ship_address']['city']}"

        # Order comment
        if self.order_data['special_instructions']:
            correction['remarks'] = self.order_data['special_instructions']
        else:
            correction['remarks'] = ''

        return correction

    def __get_product_data(self, item):
        '''Get product details.'''
        url = f"{self.server_name}/api/products/bulk_products?q[name_eq]={item['variant']['product_name']}"
        response = requests.get(url, headers=self.headers, params=self.params)
        product_data = response.json()
        return product_data

    def __make_order_item_correction(self, item):
        '''Make order item correction.'''
        correction = {}
        product_data = self.__get_product_data(item)

        try:
            product = product_data['products'][0]
        except IndexError:
            product = None

        if product:
            # Get manufacturer
            correction['manufacturer_idref'] = product['producer_id']
            correction['manufacturer_pid'] = product['variants'][0]['producer_name']

            # Get tax
            tax_category_id = product['tax_category_id']

            if tax_category_id == 1:
                tax_category = 'MwSt.-19'
                tax_rate = '19.00'
            elif tax_category_id == 2:
                tax_category = 'MwSt.-7'
                tax_rate = '7.00'
            elif tax_category_id == 3:
                tax_category = 'MwSt.-10'
                tax_rate = '10.70'
            else:
                tax_category = 'MwSt.-'
                tax_rate = '0.00'

            correction['tax_category'] = tax_category
            correction['tax_rate'] = tax_rate

        else:
            # Get manufacturer
            correction['manufacturer_idref'] = ''
            correction['manufacturer_pid'] = ''
            # Get tax
            correction['tax_category'] = 'MwSt.-'
            correction['tax_rate'] = '0.00'

        # Get EAN from google sheet
        found_sku = self.eans.loc[self.eans['sku'] == item['variant']['sku']]
        if not found_sku.empty:
            found_ean = found_sku.iloc[0]['EAN']
            if found_ean == '':
                correction['ean'] = item['variant']['sku']
            else:
                correction['ean'] = found_ean
        else:
            correction['ean'] = item['variant']['sku']

        # Fix product display name
        if item['variant']['product_name'] == item['variant']['name_to_display']:
            correction['description_short'] = f"{item['variant']['product_name']} {item['variant']['unit_to_display']}"
        else:
            correction['description_short'] = f"{item['variant']['product_name']} {item['variant']['name_to_display']} {item['variant']['unit_to_display']}"

        return correction

    def __iterate_items(self):
        '''Iterate through products.'''
        print('Products:')
        skus_wrong_format = []
        for count, item in enumerate(self.order_data['line_items'], 1):
            print(item['variant']['sku'])
            correction = self.__make_order_item_correction(item)
            # Get all skus with wrong format
            if not re.match(r'\b\w{3}\-\w{3}\-\d{3,}\b', item['variant']['sku']):
                skus_wrong_format.append({'sku': item['variant']['sku'],
                    'producer': correction['manufacturer_pid']})
            self.xml_str += get_xml_body(item, count, self.order_data, correction)

        return skus_wrong_format

    def __replace_special_chr(self, ch1, ch2):
        '''Replace char1 with char2.'''
        if ch1 in self.xml_str:
            self.xml_str = self.xml_str.replace(ch1, ch2)

    def __send_email(self, receiver, subject, body, filename, attchmnt):
        '''General send email method.'''
        smtp_server = os.environ['SMTP_SERVER']
        port = 465
        sender_email = os.environ['SMTP_SERVER_USER']
        password = os.environ['SMTP_SERVER_PASSWORD']

        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = receiver
        message['Subject'] = subject
        message['Bcc'] = receiver
        message.attach(MIMEText(body, 'plain'))

        if attchmnt:
            attachment = MIMEBase('application', 'xml')
            attachment.set_payload(attchmnt)
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}',
            )
            message.attach(attachment)

        text = message.as_string()
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver, text)

    def __send_email_wrong_sku_format(self, skus_wrong_format):
        '''Send email with wrong sku format.'''
        receiver = os.environ['EMAIL_OFN']
        subject = 'SKU Fehler in Bauernbox'
        body = 'Es gab ein paar Fehler mit:'
        for sku_wrong_format in skus_wrong_format:
            body += f"<br>SKU {sku_wrong_format['sku']}, von Produzent {sku_wrong_format['producer']}"
        body += '<br>bitte prüfen.'
        self.__send_email(receiver, subject, body, None, None)

    def __send_email_zip_not_in_range(self, order, delivery_zip):
        '''Send email if zipcode not in certain range.'''
        receiver = os.environ['EMAIL_OFN']
        subject = 'Falsche Postleitzahl in Bauernbox'
        body = f"Bestellnummer {self.order_data['number']}, Postleitzahl {delivery_zip}<br>bitte prüfen."
        self.__send_email(receiver, subject, body, None, None)

    def __send_by_email(self, filename, attchmnt):
        '''Send xml file by email.'''
        receiver = os.environ['EMAIL_OPENTRANSORDERS']
        subject = 'Opentransorders'
        body = 'Opentransorders xml files:'
        self.__send_email(receiver, subject, body, filename, attchmnt)

    def __send_to_ftp_server(self, filename, attchmnt):
        '''Send xml file to ftp server.'''
        with ftplib.FTP(os.environ['FTP_SERVER'], os.environ['FTP_USERNAME'],
                os.environ['FTP_PASSWORD']) as ftp:
            ftp.storbinary(f'STOR orders/{filename}', io.BytesIO(attchmnt))

    def __save_to_local_storage(self, tree, filename):
        '''Save to local storage.'''
        tree.write(filename, encoding="utf-8", xml_declaration=True, short_empty_elements=False)

    def generate(self):
        '''General method.'''
        self.__get_order_data()
        correction = self.__get_order_header_correction()
        self.xml_str = get_xml_header(self.order_data, correction)
        skus_wrong_format = self.__iterate_items()
        self.xml_str += get_xml_footer(self.order_data)
        self.__replace_special_chr('&', '&amp;')

        if skus_wrong_format:
            self.__send_email_wrong_sku_format(skus_wrong_format)

        if correction['delivery_zip'] not in self.postal_codes:
            self.__send_email_zip_not_in_range(self.order_data, correction['delivery_zip'])

        filename = f"opentransorder{self.order_data['number']}.xml"
        tree = ET.ElementTree(ET.fromstring(self.xml_str, ET.XMLParser(encoding='utf-8')))
        root = tree.getroot()
        attchmnt = ET.tostring(root, encoding='utf-8', method='xml')
        self.__send_by_email(filename, attchmnt)
        self.__send_to_ftp_server(filename, attchmnt)

