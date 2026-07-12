import io

from pypdf import PdfReader, PdfWriter
from pypdf._page import PageObject
from reportlab.pdfgen import canvas

from models.numbering_config import NumberingConfig


class PageNumberingService:
    """結合済みPDFの右上に「現在ページ/総ページ数」を付与する"""

    _MARGIN_RIGHT: float = 36.0
    _MARGIN_TOP: float = 24.0
    _FONT_NAME: str = "Helvetica"
    _FONT_SIZE: int = 10

    def add_page_numbers(self, writer: PdfWriter, config: NumberingConfig) -> None:
        total_pages = len(writer.pages)
        if config.start_page > total_pages:
            raise ValueError("start_page が総ページ数を超えています")

        for index, page in enumerate(writer.pages):
            page_number_in_document = index + 1
            if page_number_in_document < config.start_page:
                continue

            display_number = config.start_number + (page_number_in_document - config.start_page)
            overlay_page = self._create_overlay_page(
                width=float(page.mediabox.width),
                height=float(page.mediabox.height),
                text=f"{display_number}/{total_pages}",
            )
            page.merge_page(overlay_page)

    def _create_overlay_page(self, width: float, height: float, text: str) -> PageObject:
        buffer = io.BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=(width, height))
        pdf_canvas.setFont(self._FONT_NAME, self._FONT_SIZE)
        x = width - self._MARGIN_RIGHT
        y = height - self._MARGIN_TOP
        pdf_canvas.drawRightString(x, y, text)
        pdf_canvas.save()
        buffer.seek(0)
        return PdfReader(buffer).pages[0]
