import datetime as dt
import os
import requests


class XMLOrderTemplate:

    def __init__(self):
        pass

    def _get_xml_header(self, order, correction):
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


class XMLOrder(XMLOrderTemplate):

    xml_str = ''
    
    def __init__(self, server_name):
        self.server_name = server_name

    def _get_order_data(self, order_number, headers, params):
        url = f'{self.server_name}/api/orders/{order_number}'
        response = requests.get(url, headers=headers, params=params)
        order = response.json()

        return order
        
    def _make_data_correction(self, order):
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

    def generate(self):
        order_number = 'R324454232'
        headers = {
            'Accept': 'application/json;charset=UTF-8',
            'Content-Type': 'application/json'
        }
        params = (('token', os.environ['OPEN_FOOD_NETWORK_API_KEY']),)
        order = self._get_order_data(order_number, headers, params)
        correction = self._make_data_correction(order)
        self.xml_str = self._get_xml_header(order, correction)
