import json
import io
import os

from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import mm

from ofn_python.lib.common.core_functions import send_email


def run():
    k_rohlmann_data = {}
    with open(f'{os.environ["PATH_TO_OFN_PYTHON"]}/k_rohlmann_items.json') as json_file:
        k_rohlmann_data = json.load(json_file)

    if k_rohlmann_data:
        stream = io.BytesIO()
        doc = SimpleDocTemplate(stream, pagesize=A4, rightMargin=18, leftMargin=18, topMargin=18,
            bottomMargin=18)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='align_right', alignment=TA_RIGHT))

        body = []
        for k, v in k_rohlmann_data.items():
            print(k)
            body.append(Paragraph(f'<font size="12">Order {k}</font>', styles["Normal"]))
            body.append(Spacer(1, 12))

            p1 = Paragraph(f'<font size="8"><b>Product name</b></font>', styles["Normal"])
            p2 = Paragraph(f'<font size="8"><b>SKU</b></font>', styles["align_right"])
            p3 = Paragraph(f'<font size="8"><b>Qty</b></font>', styles["align_right"])
            p4 = Paragraph(f'<font size="8"><b>Price</b></font>', styles["align_right"])
            data = [[p1, p2, p3, p4]]

            for item in v:
                p1 = Paragraph(f'<font size="8">{item["product_name"]}</font>', styles["Normal"])
                p2 = Paragraph(f'<font size="8">{item["sku"]}</font>', styles["align_right"])
                p3 = Paragraph(f'<font size="8">{item["quantity"]}</font>', styles["align_right"])
                p4 = Paragraph(f'<font size="8">{item["price"]}</font>', styles["align_right"])
                data.append([p1, p2, p3, p4])

            t = Table(data, colWidths=(96*mm, 31*mm, 31*mm, 31*mm))
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), '#e8e8e8'),
                ('BOX', (0, 0), (-1, -1), 0.25, '#000000'),
                ('LINEBELOW', (0, 0), (-1, -2), 0.25, '#000000')
            ]))
            body.append(t)
            body.append(Spacer(1, 24))

        doc.build(body)
        pdf_file = stream.getvalue()
        stream.close()

        send_email(os.environ['EMAIL_OFN'], "Kräuterhof Rohlmann today's items", '',
            'Rohlmann.pdf', pdf_file, file_extension='pdf')

if __name__ == '__main__':
    run()
