"""HTML作成・編集ツール本体(単一HTMLファイル)を組み立てるビジネスロジック。"""

from __future__ import annotations

from pathlib import Path

from models import AppConfig

# Pythonユーザーコードを「標準出力/エラーを捕捉しつつ」実行するためのラッパー。
# 任意のユーザーコードを文字列連結でPythonソースに埋め込むと引用符の衝突や
# インジェクションのリスクがあるため、ユーザーコードは変数 __user_code 経由で
# 受け渡し、ラッパー自体は固定文字列にしている。
_PYTHON_RUN_WRAPPER = """
import io, contextlib, traceback
__stdout_buffer = io.StringIO()
__error_text = ""
try:
    with contextlib.redirect_stdout(__stdout_buffer), contextlib.redirect_stderr(__stdout_buffer):
        exec(compile(__user_code, "<python-console>", "exec"), globals())
except Exception:
    __error_text = traceback.format_exc()
__stdout_buffer_value = __stdout_buffer.getvalue()
""".strip()

# Pyodide読み込み直後に一度だけ実行する初期化コード。
# render_html()/get_html() を通じて、Pythonコード側からHTML編集パネルと
# プレビューを直接操作できるようにする橋渡し役。
_PYTHON_PRELUDE = """
import js

def render_html(html: str) -> None:
    js.setPreviewHtml(str(html))

def get_html() -> str:
    return str(js.getHtmlSource())
""".strip()

_SAMPLE_HTML_SOURCE = """<!doctype html>
<html lang="ja">
<head><meta charset="utf-8"><title>サンプル</title></head>
<body>
  <h1>ようこそ</h1>
  <p>ここを編集して「プレビュー更新」を押してください。</p>
</body>
</html>
"""

_SAMPLE_PYTHON_SOURCE = """# ここにPythonコードを書いて Ctrl+Enter (または「実行」) で実行できます。
# render_html(html) でプレビュー欄のHTMLをPythonから書き換えられます。
# get_html() で現在のHTMLソースを文字列として取得できます。

print("Pythonが実行できました")

render_html('''
<h1>Pythonから生成したHTML</h1>
<p>これはPythonコードから render_html() で書き込まれました。</p>
''')
"""


class StudioStyleSheet:
    """ツール画面の見た目(CSS)を組み立てる責務を持つクラス。"""

    def render(self) -> str:
        return """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Segoe UI", "Yu Gothic UI", sans-serif;
  background: #f3f4f6;
  color: #1f2937;
  display: flex;
  flex-direction: column;
  height: 100vh;
}
header {
  padding: 12px 20px;
  background: #111827;
  color: #f9fafb;
  display: flex;
  align-items: center;
  gap: 12px;
}
header h1 { font-size: 16px; margin: 0; }
header p { font-size: 12px; margin: 0; color: #9ca3af; }
#status-badge {
  margin-left: auto;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #f59e0b;
  color: #1f2937;
  white-space: nowrap;
}
#status-badge[data-state="ready"] { background: #22c55e; }
#status-badge[data-state="error"] { background: #ef4444; color: #fff; }
main.layout {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  padding: 10px;
  min-height: 0;
}
.column { display: flex; flex-direction: column; gap: 10px; min-height: 0; }
.panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  overflow: hidden;
  min-height: 0;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #e5e7eb;
  font-size: 13px;
  font-weight: 600;
}
.panel-header button {
  margin-left: auto;
  font-size: 12px;
  padding: 4px 10px;
  border: 1px solid #9ca3af;
  border-radius: 6px;
  background: #ffffff;
  cursor: pointer;
}
.panel-header button + button { margin-left: 6px; }
.panel-header button:disabled { opacity: 0.5; cursor: not-allowed; }
textarea {
  flex: 1;
  width: 100%;
  border: none;
  resize: none;
  padding: 10px;
  font-family: "Cascadia Code", Consolas, monospace;
  font-size: 13px;
  outline: none;
}
#preview-frame { flex: 1; border: none; background: #ffffff; }
#python-panel { flex: 1.2; }
#python-output {
  flex: 0 0 35%;
  margin: 0;
  padding: 10px;
  overflow: auto;
  background: #0b1021;
  color: #d1d5db;
  font-family: "Cascadia Code", Consolas, monospace;
  font-size: 12px;
  white-space: pre-wrap;
  border-top: 1px solid #d1d5db;
}
#python-output.error { color: #fca5a5; }
footer {
  padding: 6px 20px;
  font-size: 12px;
  color: #6b7280;
  background: #e5e7eb;
}
""".strip()


class StudioClientScript:
    """Pyodide連携・イベント処理などのJavaScriptを組み立てる責務を持つクラス。"""

    def __init__(self, python_prelude: str, python_run_wrapper: str) -> None:
        self._python_prelude = python_prelude
        self._python_run_wrapper = python_run_wrapper

    def render(self) -> str:
        prelude_js = self._as_js_string(self._python_prelude)
        wrapper_js = self._as_js_string(self._python_run_wrapper)
        return f"""
const statusBadge = document.getElementById("status-badge");
const htmlSource = document.getElementById("html-source");
const previewFrame = document.getElementById("preview-frame");
const pythonSource = document.getElementById("python-source");
const pythonOutput = document.getElementById("python-output");
const runButton = document.getElementById("btn-run");
const renderButton = document.getElementById("btn-render");
const saveButton = document.getElementById("btn-save");
const openButton = document.getElementById("btn-open");
const clearOutputButton = document.getElementById("btn-clear-output");
const fileInput = document.getElementById("file-input");

const PYTHON_PRELUDE = {prelude_js};
const PYTHON_RUN_WRAPPER = {wrapper_js};

let pyodide = null;
let pyodideReady = false;

function setStatus(text, state) {{
  statusBadge.textContent = text;
  statusBadge.dataset.state = state || "";
}}

function updatePreview() {{
  previewFrame.srcdoc = htmlSource.value;
}}

window.setPreviewHtml = function (html) {{
  htmlSource.value = html;
  updatePreview();
}};

window.getHtmlSource = function () {{
  return htmlSource.value;
}};

function enableTabIndent(textarea) {{
  textarea.addEventListener("keydown", (event) => {{
    if (event.key !== "Tab") return;
    event.preventDefault();
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    textarea.value = textarea.value.slice(0, start) + "    " + textarea.value.slice(end);
    textarea.selectionStart = textarea.selectionEnd = start + 4;
  }});
}}

async function initializePyodide() {{
  setStatus("Pyodideを読み込み中...", "loading");
  pyodide = await loadPyodide();
  await pyodide.runPythonAsync(PYTHON_PRELUDE);
  pyodideReady = true;
  runButton.disabled = false;
  setStatus("準備完了", "ready");
}}

async function runPythonCode() {{
  if (!pyodideReady) return;
  const code = pythonSource.value;
  runButton.disabled = true;
  setStatus("実行中...", "loading");
  try {{
    await pyodide.loadPackagesFromImports(code);
    pyodide.globals.set("__user_code", code);
    await pyodide.runPythonAsync(PYTHON_RUN_WRAPPER);
    const output = pyodide.globals.get("__stdout_buffer_value") || "";
    const errorText = pyodide.globals.get("__error_text") || "";
    pythonOutput.textContent = errorText ? output + "\\n" + errorText : output;
    pythonOutput.classList.toggle("error", Boolean(errorText));
  }} catch (err) {{
    pythonOutput.textContent = String(err);
    pythonOutput.classList.add("error");
  }} finally {{
    setStatus("準備完了", "ready");
    runButton.disabled = false;
  }}
}}

function downloadCurrentHtml() {{
  const blob = new Blob([htmlSource.value], {{ type: "text/html" }});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "edited.html";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}}

function openHtmlFile(file) {{
  const reader = new FileReader();
  reader.onload = () => {{
    htmlSource.value = String(reader.result || "");
    updatePreview();
  }};
  reader.readAsText(file, "utf-8");
}}

renderButton.addEventListener("click", updatePreview);
runButton.addEventListener("click", runPythonCode);
saveButton.addEventListener("click", downloadCurrentHtml);
clearOutputButton.addEventListener("click", () => {{
  pythonOutput.textContent = "";
  pythonOutput.classList.remove("error");
}});
openButton.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (event) => {{
  const file = event.target.files && event.target.files[0];
  if (file) openHtmlFile(file);
  fileInput.value = "";
}});
pythonSource.addEventListener("keydown", (event) => {{
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {{
    event.preventDefault();
    runPythonCode();
  }}
}});
enableTabIndent(htmlSource);
enableTabIndent(pythonSource);

updatePreview();
runButton.disabled = true;
initializePyodide().catch((err) => {{
  setStatus("Pyodideの読み込みに失敗しました", "error");
  pythonOutput.textContent = String(err);
  pythonOutput.classList.add("error");
}});
""".strip()

    @staticmethod
    def _as_js_string(value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace("`", "\\`")
        return f"`{escaped}`"


class StudioHtmlBuilder:
    """設定(AppConfig)から、配布用の単一HTMLドキュメント文字列を組み立てるクラス。"""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._stylesheet = StudioStyleSheet()
        self._client_script = StudioClientScript(_PYTHON_PRELUDE, _PYTHON_RUN_WRAPPER)

    def build(self) -> str:
        return (
            "<!doctype html>\n"
            f'<html lang="ja">\n{self._build_head()}\n'
            f"<body>\n{self._build_header()}\n{self._build_main()}\n"
            f"{self._build_footer()}\n{self._build_scripts()}\n"
            "</body>\n</html>\n"
        )

    def _build_head(self) -> str:
        title = self._escape(self._config.metadata.title)
        return (
            "<head>\n"
            '  <meta charset="utf-8">\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"  <title>{title}</title>\n"
            f"  <style>\n{self._stylesheet.render()}\n  </style>\n"
            "</head>"
        )

    def _build_header(self) -> str:
        title = self._escape(self._config.metadata.title)
        description = self._escape(self._config.metadata.description)
        return (
            "<header>\n"
            f"  <h1>{title}</h1>\n"
            f"  <p>{description}</p>\n"
            '  <span id="status-badge">起動中...</span>\n'
            "</header>"
        )

    def _build_main(self) -> str:
        return f"""<main class="layout">
  <div class="column">
    <section class="panel" id="html-panel">
      <div class="panel-header">
        <span>HTMLソース</span>
        <button id="btn-open" type="button">開く</button>
        <button id="btn-save" type="button">保存</button>
        <button id="btn-render" type="button">プレビュー更新</button>
      </div>
      <textarea id="html-source" spellcheck="false">{self._escape(_SAMPLE_HTML_SOURCE)}</textarea>
    </section>
    <section class="panel" id="python-panel">
      <div class="panel-header">
        <span>Pythonコンソール</span>
        <button id="btn-clear-output" type="button">出力クリア</button>
        <button id="btn-run" type="button">実行 (Ctrl+Enter)</button>
      </div>
      <textarea id="python-source" spellcheck="false">{self._escape(_SAMPLE_PYTHON_SOURCE)}</textarea>
      <pre id="python-output"></pre>
    </section>
  </div>
  <div class="column">
    <section class="panel" id="preview-panel">
      <div class="panel-header"><span>プレビュー</span></div>
      <iframe id="preview-frame" sandbox="allow-scripts"></iframe>
    </section>
  </div>
</main>
<input type="file" id="file-input" accept=".html,.htm" hidden>"""

    def _build_footer(self) -> str:
        return (
            "<footer>初回起動時のみPythonランタイムのダウンロードのため"
            "インターネット接続が必要です。以降はローカルで動作します。</footer>"
        )

    def _build_scripts(self) -> str:
        pyodide_url = self._config.pyodide.script_url
        return (
            f'<script src="{pyodide_url}"></script>\n'
            f"<script>\n{self._client_script.render()}\n</script>"
        )

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


class StudioFileWriter:
    """組み立てたHTML文字列をファイルへ書き出す責務を持つクラス。"""

    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path

    @property
    def output_path(self) -> Path:
        return self._output_path

    @output_path.setter
    def output_path(self, value: Path) -> None:
        if value.suffix.lower() != ".html":
            raise ValueError("output_path は .html 拡張子で終わる必要があります。")
        self._output_path = value

    def write(self, content: str) -> Path:
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(content, encoding="utf-8")
        return self._output_path
