from pathlib import Path

import pytest
from PySide6.QtWidgets import QTextEdit

from ui_reference import scale_document_fonts


def _sample_font_sizes(editor: QTextEdit, limit: int = 8) -> list[float]:
    sizes: list[float] = []
    block = editor.document().begin()
    while block.isValid() and len(sizes) < limit:
        iterator = block.begin()
        while not iterator.atEnd() and len(sizes) < limit:
            fragment = iterator.fragment()
            if fragment.isValid():
                size = fragment.charFormat().fontPointSize()
                if size > 0:
                    sizes.append(size)
            iterator += 1
        block = block.next()
    return sizes


@pytest.mark.usefixtures("qapp")
def test_scale_document_fonts_scales_inline_html_sizes():
    editor = QTextEdit()
    html = Path("data/reference/consonants.html").read_text(encoding="utf-8")
    editor.setHtml(html)
    before = _sample_font_sizes(editor)
    assert before
    assert all(size == before[0] for size in before)

    scale_document_fonts(editor, 150)
    after = _sample_font_sizes(editor)
    assert after
    assert after[0] == before[0] * 1.5
