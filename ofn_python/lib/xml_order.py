import datetime as dt
import ftplib
import os
import re
import requests
import xml.etree.ElementTree as ET


class XMLOrderTemplate:

    def __init__(self):
        pass

    def _get_order_header(self, order, correction):
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<ORDER type="standard" version="2.1" xmlns="http://www.opentrans.org/XMLSchema/2.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opentrans.org/XMLSchema/2.1 opentrans_2_1.xsd" xmlns:bmecat="http://www.bmecat.org/bmecat/2005" xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsig="http://www.w3.org/2000/09/xmldsig#">
<ORDER_HEADER>
<CONTROL_INFO>
<GENERATOR_INFO></GENERATOR_INFO>
<GENERATION_DATE></GENERATION_DATE>
</CONTROL_INFO>
<ORDER_INFO>
<ORDER_ID>{order['number']}</ORDER_ID>
<ORDER_DATE>{correction['completed_at']}</ORDER_DATE>
<PARTIES>
    <PARTY>
        <bmecat:PARTY_ID type="buyer_specific">{order['user_id']}</bmecat:PARTY_ID>
        <PARTY_ROLE>buyer</PARTY_ROLE>
        <ADDRESS>
            <bmecat:NAME>{order['full_name']}</bmecat:NAME>
            <bmecat:STREET>{order['bill_address']['address1']}</bmecat:STREET>
            <bmecat:ZIP>{order['bill_address']['zipcode']}</bmecat:ZIP>
            <bmecat:CITY>{order['bill_address']['city']}</bmecat:CITY>
            <bmecat:STATE>{order['bill_address']['state_name']}</bmecat:STATE>
            <bmecat:COUNTRY>{order['bill_address']['country_name']}</bmecat:COUNTRY>
            <bmecat:COUNTRY_CODED>DE</bmecat:COUNTRY_CODED>
            <bmecat:PHONE type="office">{order['phone']}</bmecat:PHONE>
            <bmecat:EMAIL>{order['email']}</bmecat:EMAIL>
        </ADDRESS>
    </PARTY>
    <PARTY>
        <bmecat:PARTY_ID type="supplier_specific">{order['user_id']}</bmecat:PARTY_ID>
        <PARTY_ROLE>supplier</PARTY_ROLE>
        <ADDRESS>
            <bmecat:STREET></bmecat:STREET>
            <bmecat:STREET></bmecat:STREET>
            <bmecat:ZIP></bmecat:ZIP>
            <bmecat:CITY></bmecat:CITY>
            <bmecat:STATE></bmecat:STATE>
            <bmecat:COUNTRY></bmecat:COUNTRY>
            <bmecat:COUNTRY_CODED>DE</bmecat:COUNTRY_CODED>
            <bmecat:PHONE type="office"></bmecat:PHONE>
            <bmecat:EMAIL></bmecat:EMAIL>
        </ADDRESS>
    </PARTY>
    <PARTY>
        <bmecat:PARTY_ID type="delivery_specific">{order['ship_address']['id']}</bmecat:PARTY_ID>
        <PARTY_ROLE>delivery</PARTY_ROLE>
        <ADDRESS>
            <bmecat:NAME>{order['ship_address']['firstname']} {order['ship_address']['lastname']}</bmecat:NAME>
            <bmecat:STREET>{correction['delivery_street']}</bmecat:STREET>
            <bmecat:ZIP>{correction['delivery_zip']}</bmecat:ZIP>
            <bmecat:CITY>{correction['delivery_city']}</bmecat:CITY>
            <bmecat:STATE>{order['ship_address']['state_name']}</bmecat:STATE>
            <bmecat:COUNTRY>{order['ship_address']['country_name']}</bmecat:COUNTRY>
            <bmecat:COUNTRY_CODED>DE</bmecat:COUNTRY_CODED>
            <bmecat:PHONE type="office">{order['ship_address']['phone']}</bmecat:PHONE>
            <bmecat:EMAIL>{order['email']}</bmecat:EMAIL>
        </ADDRESS>
    </PARTY>
</PARTIES>
<CUSTOMER_ORDER_REFERENCE>
    <ORDER_ID>{order['number']}</ORDER_ID>
    <ORDER_DATE>{correction['completed_at']}</ORDER_DATE>
    <CUSTOMER_IDREF type="buyer_specific">{order['user_id']}</CUSTOMER_IDREF>
</CUSTOMER_ORDER_REFERENCE>
<ORDER_PARTIES_REFERENCE>
    <bmecat:BUYER_IDREF type="buyer_specific">{order['user_id']}</bmecat:BUYER_IDREF>
    <bmecat:SUPPLIER_IDREF type="supplier_specific">{order['distributor']['id']}</bmecat:SUPPLIER_IDREF>
    <INVOICE_RECIPIENT_IDREF type="buyer_specific">{order['user_id']}</INVOICE_RECIPIENT_IDREF>
    <SHIPMENT_PARTIES_REFERENCE>
        <DELIVERER_IDREF type="delivery_specific">{order['user_id']}</DELIVERER_IDREF>
    </SHIPMENT_PARTIES_REFERENCE>
</ORDER_PARTIES_REFERENCE>
<bmecat:CURRENCY>EUR</bmecat:CURRENCY>
<PARTIAL_SHIPMENT_ALLOWED>TRUE</PARTIAL_SHIPMENT_ALLOWED>
<bmecat:TRANSPORT>
    <bmecat:INCOTERM></bmecat:INCOTERM>
    <bmecat:LOCATION>{correction['transport_location']}</bmecat:LOCATION>
    <bmecat:TRANSPORT_REMARK>{order['shipping_method']['name']}</bmecat:TRANSPORT_REMARK>
</bmecat:TRANSPORT>
<REMARKS type="customType">{correction['remarks']}</REMARKS>
</ORDER_INFO>
</ORDER_HEADER>
<ORDER_ITEM_LIST>"""

    def _get_order_item(self, item, count, order, correction):
        return f"""
<ORDER_ITEM>
<LINE_ITEM_ID>{count}</LINE_ITEM_ID>
<PRODUCT_ID>
    <bmecat:SUPPLIER_PID type="supplier_specific">{item['variant']['sku']}</bmecat:SUPPLIER_PID>
    <bmecat:SUPPLIER_IDREF type="supplier_specific">{order['distributor']['id']}</bmecat:SUPPLIER_IDREF>
    <bmecat:INTERNATIONAL_PID type="ean">{correction['ean']}</bmecat:INTERNATIONAL_PID>
    <bmecat:BUYER_PID type="buyer_specific">{order['user_id']}</bmecat:BUYER_PID>
    <bmecat:DESCRIPTION_SHORT lang="deu">{correction['description_short']}</bmecat:DESCRIPTION_SHORT>
    <MANUFACTURER_INFO>
        <bmecat:MANUFACTURER_IDREF type="manufacturer_specific">{correction['manufacturer_idref']}</bmecat:MANUFACTURER_IDREF>
        <bmecat:MANUFACTURER_PID>{correction['manufacturer_pid']}</bmecat:MANUFACTURER_PID>
        <bmecat:MANUFACTURER_TYPE_DESCR lang="eng"></bmecat:MANUFACTURER_TYPE_DESCR>
    </MANUFACTURER_INFO>
    </PRODUCT_ID>
<QUANTITY>{item['quantity']}</QUANTITY>
<bmecat:ORDER_UNIT></bmecat:ORDER_UNIT>
<PRODUCT_PRICE_FIX>
    <bmecat:PRICE_AMOUNT>{item['price']}</bmecat:PRICE_AMOUNT>
    <TAX_DETAILS_FIX>
        <bmecat:CALCULATION_SEQUENCE>1</bmecat:CALCULATION_SEQUENCE>
        <bmecat:TAX_CATEGORY>{correction['tax_category']}</bmecat:TAX_CATEGORY>
        <bmecat:TAX_TYPE>vat</bmecat:TAX_TYPE>
        <bmecat:TAX>0.0</bmecat:TAX>
        <TAX_AMOUNT>0.0</TAX_AMOUNT>
        <TAX_BASE>0.0</TAX_BASE>
    </TAX_DETAILS_FIX>
</PRODUCT_PRICE_FIX>
<PRICE_LINE_AMOUNT>{float(item['price']) * float(item['quantity'])}</PRICE_LINE_AMOUNT>
<REMARKS type="customRemark" lang="deu"></REMARKS>
</ORDER_ITEM>"""

    def _get_order_summary(self, order):
        return f"""
</ORDER_ITEM_LIST>
<ORDER_SUMMARY>
<TOTAL_ITEM_NUM>{len(order['line_items'])}</TOTAL_ITEM_NUM>
<TOTAL_AMOUNT>{order['total']}</TOTAL_AMOUNT>
</ORDER_SUMMARY>
</ORDER>"""


class XMLOrder(XMLOrderTemplate):

    xml_str = ''
    
    def __init__(self, server_name):
        self.server_name = server_name

    def _get_order_data(self, order_number, headers, params):
        '''Get order details.'''
        url = f'{self.server_name}/api/orders/{order_number}'
        response = requests.get(url, headers=headers, params=params)
        return response

    def _make_order_header_correction(self, order):
        '''Make order header correction.'''
        correction = {}
        correction['completed_at'] = dt.datetime.strptime(order['completed_at'], '%B %d, %Y').strftime(
            '%Y-%m-%dT%H:%M:%S')

        if 'Boxenstopp Schiffahrter Damm' in order['shipping_method']['name']:
            correction['transport_location'] = 'IBS BüroTipp!, Schiffahrter Damm 24, 48145 Münster'
            correction['delivery_street'] = 'Schiffahrter Damm 24'
            correction['delivery_zip'] = '48145'
            correction['delivery_city'] = 'Münster'
        elif 'Boxenstopp Albachten' in order['shipping_method']['name']:
            correction['transport_location'] = 'Hofladen Freitag, Sendener Stiege 32, 48163 Münster'
            correction['delivery_street'] = 'Sendener Stiege 32'
            correction['delivery_zip'] = '48163'
            correction['delivery_city'] = 'Münster'
        else:
            correction['transport_location'] = f"{order['ship_address']['firstname']} {order['ship_address']['lastname']}, {order['ship_address']['address1']}, {order['ship_address']['zipcode']} {order['ship_address']['city']}"
            correction['delivery_street'] = f"{order['ship_address']['address1']}"
            correction['delivery_zip'] = f"{order['ship_address']['zipcode']}"
            correction['delivery_city'] = f"{order['ship_address']['city']}"

        # Order comment
        if order['special_instructions']:
            correction['remarks'] = order['special_instructions']
        else:
            correction['remarks'] = ''

        return correction

    def _get_product_data(self, item, headers, params):
        '''Get product details.'''
        url = f"{self.server_name}/api/products/bulk_products?q[name_eq]={item['variant']['product_name']}"
        response = requests.get(url, headers=headers, params=params)
        return response

    def _make_order_item_correction(self, item, eans, headers, params):
        '''Make order item correction.'''
        correction = {}

        # Get manufacturer from product details
        response = self._get_product_data(item, headers, params)

        try:
            product = response.json()['products'][0]
        except IndexError:
            product = None

        if product:
            correction['manufacturer_idref'] = product['producer_id']
            correction['manufacturer_pid'] = product['variants'][0]['producer_name']
        else:
            correction['manufacturer_idref'] = ''
            correction['manufacturer_pid'] = ''

        # Get EAN and tax category from google sheet
        found_sku = eans.loc[eans['sku'] == item['variant']['sku']]
        if not found_sku.empty:
            correction['tax_category'] = f"{found_sku.iloc[0]['tax_category']}"
            found_ean = found_sku.iloc[0]['EAN']

            if found_ean == '':
                correction['ean'] = item['variant']['sku']
            else:
                correction['ean'] = found_ean
        else:
            correction['tax_category'] = ''
            correction['ean'] = item['variant']['sku']

        # Fix product display name
        if item['variant']['product_name'] == item['variant']['name_to_display']:
            correction['description_short'] = f"{item['variant']['product_name']} {item['variant']['unit_to_display']}"
        else:
            correction['description_short'] = f"{item['variant']['product_name']} {item['variant']['name_to_display']} {item['variant']['unit_to_display']}"

        return correction

    def _iterate_items(self, order, eans, headers, params):
        '''Iterate through products.'''
        print('Products:')
        skus_wrong_format = []
        for count, item in enumerate(order['line_items'], 1):
            print(item['variant']['sku'])
            order_item_correction = self._make_order_item_correction(item, eans, headers, params)
            # Get all skus with wrong format
            if not re.match(r'\b\w{3}\-\w{3}\-\d{3,}\b', item['variant']['sku']):
                skus_wrong_format.append({'sku': item['variant']['sku'],
                    'producer': order_item_correction['manufacturer_pid']})
            self.xml_str += self._get_order_item(item, count, order, order_item_correction)

        return skus_wrong_format

    def _replace_special_chr(self, ch1, ch2):
        '''Replace char1 with char2.'''
        if ch1 in self.xml_str:
            self.xml_str = self.xml_str.replace(ch1, ch2)

    def _send_email_wrong_sku_format(self, skus_wrong_format):
        '''Send email with wrong sku format'''
        email_subject = 'SKU Fehler in Münsterländer Bauernbox'
        email_body = 'Es gab ein paar Fehler mit:'
        for sku_wrong_format in skus_wrong_format:
            email_body += f"<br>SKU {sku_wrong_format['sku']}, von Produzent {sku_wrong_format['producer']}"
        email_body += '<br>bitte prüfen.'
        # send_email([os.environ['EMAIL_HENDIRK_OFN']], email_subject, email_body)

    def _send_email_zip_not_in_range(self, order, delivery_zip):
        '''Send email if zipcode not in certain range.'''
        email_subject = 'Falsche Postleitzahl in Münsterländer Bauernbox'
        email_body = f"Bestellnummer {order['number']}, Postleitzahl {delivery_zip}"
        email_body += '<br>bitte prüfen.'
        # send_email(os.environ['EMAIL_HENDIRK_OFN']], email_subject, email_body)

    def _send_by_email(self, filename, tree_b_str):
        '''Send xml file by email.'''
        print()
        # send_email([os.environ['EMAIL_OPENTRANSORDERS']], 'Opentransorders', 'Opentransorders xml files:',
        #     attachment=[filename, tree_b_str, 'application/xml'])

    def _send_to_ftp_server(self, filename, tree_b_str):
        '''Send xml file to ftp server.'''
        with ftplib.FTP(os.environ['BAUERNBOX_FTP_SERVER'], os.environ['BAUERNBOX_FTP_USERNAME'],
                os.environ['BAUERNBOX_FTP_PASSWORD']) as ftp:
            ftp.storbinary(f'STOR orders/{filename}', io.BytesIO(tree_b_str))

    def _save_to_local_storage(self, tree, filename):
        '''Save to local storage.'''
        tree.write(filename, encoding="utf-8", xml_declaration=True, short_empty_elements=False)

    def generate(self, order_number, headers, params, eans, postal_codes):
        order = self._get_order_data(order_number, headers, params).json()
        order_header_correction = self._make_order_header_correction(order)
        self.xml_str = self._get_order_header(order, order_header_correction)
        skus_wrong_format = self._iterate_items(order, eans, headers, params)
        self.xml_str += self._get_order_summary(order)
        self._replace_special_chr('&', '&amp;')

        if skus_wrong_format:
            self._send_email_wrong_sku_format(skus_wrong_format)

        if order_header_correction['delivery_zip'] not in postal_codes:
            self._send_email_zip_not_in_range(order, order_header_correction['delivery_zip'])

        filename = f"opentransorder{order['number']}.xml"
        tree = ET.ElementTree(ET.fromstring(self.xml_str, ET.XMLParser(encoding='utf-8')))
        root = tree.getroot()
        tree_b_str = ET.tostring(root, encoding='utf-8', method='xml')
        # self._send_by_email(filename, tree_b_str)
        # self._send_to_ftp_server(filename, tree_b_str)

