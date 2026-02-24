#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中二病也要造汉字 - SVG 导出工具"""

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from pathlib import Path
from datetime import datetime


def export_char_svg(font_path, char, output_dir='output_svg'):

    font = TTFont(font_path)
    glyphSet = font.getGlyphSet()
    cmap = font.getBestCmap()

    glyph_name = cmap.get(ord(char))
    if not glyph_name or glyph_name not in glyphSet:
        print(f"❌ 未找到字符：{char}")
        font.close()
        return None

    glyph = glyphSet[glyph_name]

    pen = SVGPathPen(glyphSet)
    glyph.draw(pen)
    path_data = pen.getCommands()

    font.close()

    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="500" height="500" viewBox="0 -200 1000 1400">
    <path d="{path_data}" fill="#000" transform="matrix(1,0,0,-1,0,1000)"/>
</svg>'''

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'{char}_{timestamp}.svg'

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    print(f"✓ {char} → {output_file.name}")

    return output_file


def interactive_mode():
    print("\n" + "=" * 60)
    print("🔤 中二病也要造汉字 - SVG 导出工具")
    print("=" * 60)

    current_dir = Path(__file__).parent
    font_path = current_dir / 'fonts' / 'NotoSerifSC-VariableFont_wght.ttf'

    if not font_path.exists():
        print(f"\n❌ 字体文件不存在：{font_path}")
        return

    print(f"\n✓ 字体：{font_path.name}")
    output_dir = input("\n输出目录（默认 output_svg）：").strip() or 'output_svg'

    while True:
        print("\n" + "-" * 60)
        char = input("请输入汉字（输入 q 退出）：").strip()

        if char.lower() == 'q':
            print("\n👋 再见！")
            break

        if not char:
            print("❌ 输入不能为空")
            continue

        char_list = char.replace(',', ' ').replace(',', ' ').split()
        for c in char_list:
            export_char_svg(font_path, c, output_dir)

    print(f"\n📁 输出目录：{Path(output_dir).absolute()}")


if __name__ == "__main__":
    interactive_mode()