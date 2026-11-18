# docx_io.py — Word(.docx) 与 QTextEdit 富文本的双向转换
# 读取：docx 段落/字体格式 -> HTML（标题/列表/粗斜下划线）
# 保存：QTextDocument 块/片段 -> python-docx 文档
# 局限：表格读入时简化为文本行，嵌入图片不读取（写入时保留已加载的简单排版）

import html as _html

from docx import Document
from PySide6.QtGui import QFont, QTextListFormat


def _runs_html(paragraph) -> str:
    """把一个 docx 段落的 runs 转成带 <b>/<i>/<u> 的 HTML 片段。"""
    out = []
    for run in paragraph.runs:
        t = _html.escape(run.text)
        if not t:
            continue
        if run.underline:
            t = f"<u>{t}</u>"
        if run.italic:
            t = f"<i>{t}</i>"
        if run.bold:
            t = f"<b>{t}</b>"
        out.append(t)
    return "".join(out) if out else "<br>"


def load_docx_to_html(path: str) -> str:
    """读取 .docx 返回可注入 QTextEdit.setHtml 的 HTML 字符串。"""
    doc = Document(path)
    parts = []
    open_list = None  # None | 'ul' | 'ol'

    def close_list():
        nonlocal open_list
        if open_list:
            parts.append(f"</{open_list}>")
            open_list = None

    for para in doc.paragraphs:
        style = (para.style.name if para.style is not None else "") or ""
        inner = _runs_html(para)
        if style.startswith("Heading") or style.startswith(u"标题"):
            try:
                level = min(max(int(style.split()[-1]), 1), 4)
            except ValueError:
                level = 2
            close_list()
            parts.append(f"<h{level}>{inner}</h{level}>")
        elif "List" in style or u"列表" in style or "Bullet" in style:
            ordered = "Number" in style or u"编号" in style
            tag = "ol" if ordered else "ul"
            if open_list != tag:
                close_list()
                parts.append(f"<{tag}>")
                open_list = tag
            parts.append(f"<li>{inner}</li>")
        else:
            close_list()
            parts.append(f"<p>{inner}</p>")
    close_list()

    # 表格简化为文本行，附在文末
    for table in doc.tables:
        parts.append("<p><br></p>")
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            parts.append("<p>" + _html.escape("  |  ".join(cells)) + "</p>")

    return "".join(parts)


def save_docx_from_qdocument(qdocument, path: str) -> None:
    """把 QTextDocument 的块结构写回 .docx 文件。"""
    doc = Document()
    block = qdocument.firstBlock()
    while block.isValid():
        fmt = block.blockFormat()
        text_list = block.textList()
        heading = fmt.headingLevel() if hasattr(fmt, "headingLevel") else 0

        if text_list is not None:
            style_enum = text_list.format().style()
            ordered = style_enum in (
                QTextListFormat.Style.ListDecimal,
                QTextListFormat.Style.ListLowerAlpha,
                QTextListFormat.Style.ListUpperAlpha,
            )
            p = doc.add_paragraph(style="List Number" if ordered else "List Bullet")
        elif heading >= 1:
            p = doc.add_paragraph(style=f"Heading {min(heading, 4)}")
        else:
            p = doc.add_paragraph()

        wrote_any = False
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            t = frag.text()
            if t:
                cf = frag.charFormat()
                run = p.add_run(t)
                run.bold = cf.fontWeight() >= 600
                run.italic = cf.fontItalic()
                run.underline = cf.fontUnderline()
                wrote_any = True
            it += 1
        if not wrote_any:
            p.add_run("")  # 保留空行段落
        block = block.next()

    doc.save(path)
