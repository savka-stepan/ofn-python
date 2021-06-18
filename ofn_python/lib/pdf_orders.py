import io

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.units import mm


class PDFOrder:
    def __init__(self, supplier_id, styles):
        self.stream = io.BytesIO()
        self.doc = SimpleDocTemplate(
            self.stream,
            pagesize=A4,
            rightMargin=18,
            leftMargin=18,
            topMargin=18,
            bottomMargin=18,
        )
        self.data = []
        self.body = []
        self.supplier_name = ""
        self.supplier_id = supplier_id
        self.styles = styles

    def add_table_header(self):
        p1 = Paragraph(f'<font size="8"><b>Product name</b></font>', self.styles["Normal"])
        p2 = Paragraph(f'<font size="8"><b>SKU</b></font>', self.styles["align_right"])
        p3 = Paragraph(f'<font size="8"><b>Qty</b></font>', self.styles["align_right"])
        p4 = Paragraph(f'<font size="8"><b>Price</b></font>', self.styles["align_right"])
        self.data = [[p1, p2, p3, p4]]

    def add_table(self, order_no, customer_name, order_period):
        self.body.append(
            Paragraph(
                f'<font size="12">{order_no}, {customer_name}, {order_period}</font>', self.styles["Normal"]
            )
        )
        self.body.append(Spacer(1, 12))

        table = Table(self.data, colWidths=(96 * mm, 31 * mm, 31 * mm, 31 * mm))
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), "#e8e8e8"),
                    ("BOX", (0, 0), (-1, -1), 0.25, "#000000"),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.25, "#000000"),
                ]
            )
        )
        self.body.append(table)
        self.body.append(Spacer(1, 24))

    def close_stream(self):
        self.stream.close()
