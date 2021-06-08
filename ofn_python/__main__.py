from ofn_python.scripts import (
    generate_xml,
    get_products,
    generate_pdf_invoice,
    send_email_rohlmann,
    update_stock_level,
)


def main():
    # generate_xml.run([36,])
    # get_products.run()
    # generate_pdf_invoice.run()
    send_email_rohlmann.run()
    # update_stock_level.run()


if __name__ == "__main__":
    main()
