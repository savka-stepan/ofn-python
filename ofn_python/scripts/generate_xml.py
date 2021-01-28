from ofn_python.lib.xml_order import XMLOrder


def run():
    xml_order = XMLOrder('https://openfoodnetwork.de')
    xml_order.generate()
    print(xml_order.xml_str)