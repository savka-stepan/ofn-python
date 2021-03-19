def get_xml_header(order, correction):
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
        <bmecat:PARTY_ID type="supplier_specific">{order['distributor']['id']}</bmecat:PARTY_ID>
        <PARTY_ROLE>supplier</PARTY_ROLE>
        <ADDRESS>
            <bmecat:NAME>{order['distributor_name']}</bmecat:NAME>
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


def get_xml_body(item, count, order, correction):
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
        <bmecat:TAX>{correction['tax_rate']}</bmecat:TAX>
        <TAX_AMOUNT>{round(float(item['price']) * float(correction['tax_rate']) / 100.0, 2)}</TAX_AMOUNT>
        <TAX_BASE>0.0</TAX_BASE>
    </TAX_DETAILS_FIX>
</PRODUCT_PRICE_FIX>
<PRICE_LINE_AMOUNT>{float(item['price']) * float(item['quantity'])}</PRICE_LINE_AMOUNT>
<REMARKS type="customRemark" lang="deu"></REMARKS>
</ORDER_ITEM>"""


def get_xml_footer(order):
    return f"""
</ORDER_ITEM_LIST>
<ORDER_SUMMARY>
<TOTAL_ITEM_NUM>{len(order['line_items'])}</TOTAL_ITEM_NUM>
<TOTAL_AMOUNT>{order['total']}</TOTAL_AMOUNT>
</ORDER_SUMMARY>
</ORDER>"""
