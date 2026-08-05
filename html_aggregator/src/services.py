import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Tuple

from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, PageBreak, Paragraph, SimpleDocTemplate

from models import AggregationConfig, HtmlPage, PageRole


class ZipArchiveRepository:
    """ZIPファイルの展開・後片付けというファイルシステムI/Oのみを担当する"""

    def extract(self, zip_path: Path) -> Path:
        if not zip_path.is_file():
            raise FileNotFoundError(f"ZIPファイルが見つかりません: {zip_path}")
        if not zipfile.is_zipfile(zip_path):
            raise ValueError(f"有効なZIPファイルではありません: {zip_path}")

        work_dir = Path(tempfile.mkdtemp(prefix="html_aggregator_"))
        with zipfile.ZipFile(zip_path) as archive:
            self._validate_members(archive, work_dir)
            archive.extractall(work_dir)
        return work_dir

    def cleanup(self, work_dir: Path) -> None:
        shutil.rmtree(work_dir, ignore_errors=True)

    def _validate_members(self, archive: zipfile.ZipFile, work_dir: Path) -> None:
        resolved_root = work_dir.resolve()
        for member in archive.infolist():
            target = (work_dir / member.filename).resolve()
            if not target.is_relative_to(resolved_root):
                raise ValueError(f"不正なパスを含むZIPエントリです: {member.filename}")


class InputSourceResolverService:
    """入力パスがZIPかフォルダかを判定し、探索対象のルートディレクトリを解決する"""

    def __init__(self, zip_repository: ZipArchiveRepository) -> None:
        self._zip_repository = zip_repository

    def resolve(self, input_path: Path) -> Tuple[Path, bool]:
        if input_path.is_dir():
            return input_path, False
        if input_path.is_file():
            return self._zip_repository.extract(input_path), True
        raise FileNotFoundError(f"フォルダまたはZIPファイルが見つかりません: {input_path}")

    def cleanup(self, root_dir: Path, should_cleanup: bool) -> None:
        if should_cleanup:
            self._zip_repository.cleanup(root_dir)


class HtmlFileRepository:
    """展開済みディレクトリ配下のHTMLファイル探索というファイルシステムI/Oのみを担当する"""

    _HTML_SUFFIXES: Tuple[str, ...] = (".html", ".htm")

    def find_html_files(self, root_dir: Path) -> List[Path]:
        if not root_dir.is_dir():
            raise NotADirectoryError(f"{root_dir} はフォルダではありません")
        return sorted(
            path for path in root_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in self._HTML_SUFFIXES
        )


class MainPageClassifierService:
    """探索されたHTML群からメインHTMLとサブHTML群を判定する"""

    def __init__(self, config: AggregationConfig) -> None:
        self._config = config

    def classify(self, html_paths: List[Path]) -> Tuple[Path, List[Path]]:
        if not html_paths:
            raise ValueError("HTMLファイルが1件も見つかりませんでした")

        for candidate_name in self._config.main_file_candidates:
            for path in html_paths:
                if path.name.lower() == candidate_name.lower():
                    return path, [p for p in html_paths if p != path]

        main_path, *sub_paths = html_paths
        return main_path, sub_paths


class SubPageOrderingService:
    """メインHTML内のリンク出現順にサブHTMLを並び替える"""

    def order(self, main_path: Path, sub_paths: List[Path], encoding: str) -> List[Path]:
        raw_html = main_path.read_text(encoding=encoding, errors="ignore")
        soup = BeautifulSoup(raw_html, "html.parser")

        link_order: List[Path] = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].split("#")[0]
            if not href or href.startswith(("http://", "https://", "mailto:")):
                continue
            link_order.append((main_path.parent / href).resolve())

        def sort_key(path: Path) -> int:
            resolved = path.resolve()
            return link_order.index(resolved) if resolved in link_order else len(link_order)

        return sorted(sub_paths, key=sort_key)


class HtmlTextExtractionService:
    """HTMLファイルからタイトルと本文テキストを抽出する"""

    def __init__(self, config: AggregationConfig) -> None:
        self._config = config

    def extract(self, html_path: Path, root_dir: Path, role: PageRole) -> HtmlPage:
        raw_html = html_path.read_text(encoding=self._config.encoding, errors="ignore")
        soup = BeautifulSoup(raw_html, "html.parser")

        title = soup.title.get_text(strip=True) if soup.title else html_path.stem
        body = soup.body if soup.body else soup
        text = self._normalize_whitespace(body.get_text(separator="\n"))

        return HtmlPage(
            relative_path=html_path.relative_to(root_dir),
            role=role,
            title=title,
            text=text,
        )

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        lines = (line.strip() for line in text.splitlines())
        return "\n".join(line for line in lines if line)


class DocumentAggregationService:
    """複数のHtmlPageを1つのテキストドキュメントへ集約する"""

    def __init__(self, config: AggregationConfig) -> None:
        self._config = config

    def build(self, pages: List[HtmlPage]) -> str:
        sections = [self._format_section(page) for page in pages]
        return self._config.section_separator.join(sections)

    @staticmethod
    def _format_section(page: HtmlPage) -> str:
        header = f"[{page.role_label}] {page.title} ({page.relative_path.as_posix()})"
        return f"{header}\n{page.text}"


class _OutlineBookmarkFlowable(Flowable):
    """PDFのしおり(アウトライン)を1件登録するだけの、描画領域を持たないFlowable"""

    def __init__(self, key: str, title: str) -> None:
        super().__init__()
        self._key = key
        self._title = title

    def wrap(self, available_width: float, available_height: float) -> Tuple[float, float]:
        return 0.0, 0.0

    def draw(self) -> None:
        self.canv.bookmarkPage(self._key)
        self.canv.addOutlineEntry(self._title, self._key, level=0, closed=False)


class PdfDocumentBuilderService:
    """複数のHtmlPageを、しおり付きの1つのPDFへ集約する"""

    _PAGE_SIZE = A4
    _MARGIN = 20 * mm

    def __init__(self) -> None:
        base_styles = getSampleStyleSheet()
        self._title_style = ParagraphStyle(
            "SectionTitle", parent=base_styles["Heading1"], spaceAfter=12,
        )
        self._body_style = ParagraphStyle(
            "SectionBody", parent=base_styles["BodyText"], leading=16, spaceAfter=6,
        )

    def build(self, pages: List[HtmlPage], output_path: Path) -> None:
        document = SimpleDocTemplate(
            str(output_path),
            pagesize=self._PAGE_SIZE,
            leftMargin=self._MARGIN,
            rightMargin=self._MARGIN,
            topMargin=self._MARGIN,
            bottomMargin=self._MARGIN,
        )
        document.build(self._build_flowables(pages))

    def _build_flowables(self, pages: List[HtmlPage]) -> List[Flowable]:
        flowables: List[Flowable] = []
        last_index = len(pages) - 1
        for index, page in enumerate(pages):
            flowables.extend(self._build_section_flowables(index, page))
            if index != last_index:
                flowables.append(PageBreak())
        return flowables

    def _build_section_flowables(self, index: int, page: HtmlPage) -> List[Flowable]:
        section_title = f"[{page.role_label}] {page.title}"
        flowables: List[Flowable] = [
            _OutlineBookmarkFlowable(key=f"section-{index}", title=section_title),
            Paragraph(self._escape(section_title), self._title_style),
        ]
        flowables.extend(
            Paragraph(self._escape(line), self._body_style)
            for line in page.text.split("\n")
            if line.strip()
        )
        return flowables

    @staticmethod
    def _escape(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
