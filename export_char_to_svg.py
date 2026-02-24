#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中二病也要造汉字 - 汉字转svg"""

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
import json
import os
import sys


class FontPathExtractor:
    def __init__(self, font_path):
        if not os.path.exists(font_path):
            print(f"❌ 错误：字体文件不存在：{font_path}")
            print(f"   当前工作目录：{os.getcwd()}")
            sys.exit(1)

        self.font_path = font_path
        print(f"✓ 正在加载字体：{os.path.basename(font_path)}")

        try:
            self.font = TTFont(font_path)
            self.glyphSet = self.font.getGlyphSet()
            self.cmap = self.font.getBestCmap()
            print(f"✓ 字体加载成功")
            print(f"  - 字形数量：{len(self.glyphSet)}")
            print(f"  - 字符映射：{len(self.cmap)}")
        except Exception as e:
            print(f"❌ 字体加载失败：{e}")
            sys.exit(1)

    def unicode_to_glyph_name(self, unicode_char):
        code_point = ord(unicode_char)
        return self.cmap.get(code_point)

    def get_svg_path(self, glyph_name):
        if glyph_name not in self.glyphSet:
            return None

        try:
            glyph = self.glyphSet[glyph_name]
            pen = SVGPathPen(self.glyphSet)
            glyph.draw(pen)
            return pen.getCommands()
        except Exception as e:
            print(f"⚠ 提取失败 {glyph_name}: {e}")
            return None

    def extract_radicals(self, char_list, output_json='radicals.json'):
        result = {}
        success_count = 0

        print(f"\n开始提取 {len(char_list)} 个字符...")
        print("-" * 60)

        for char in char_list:
            glyph_name = self.unicode_to_glyph_name(char)
            if glyph_name:
                path_data = self.get_svg_path(glyph_name)
                if path_data:
                    result[char] = {
                        'glyph_name': glyph_name,
                        'path': path_data,
                        'unicode': f"U+{ord(char):04X}"
                    }
                    success_count += 1
                    print(f"✓ {char} ({glyph_name})")
                else:
                    print(f"⚠ {char} - 路径为空")
            else:
                print(f"⚠ {char} - 未找到字形")

        print("-" * 60)
        print(f"✓ 成功提取：{success_count}/{len(char_list)}")

        output_path = os.path.abspath(output_json)
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"✓ 已保存至：{output_path}")
        return result


if __name__ == "__main__":
    radicals_and_chars = [
        '白', '泊', '车'
    ]

    current_dir = os.path.dirname(os.path.abspath(__file__))

    font_path = os.path.join(current_dir, 'fonts', 'NotoSerifSC-VariableFont_wght.ttf')

    if not os.path.exists(font_path):
        font_path = os.path.join(current_dir, 'NotoSerifSC-VariableFont_wght.ttf')

    print("=" * 60)
    print("🔤 思源宋体路径提取工具")
    print("=" * 60)
    print(f"字体路径：{font_path}")
    print("=" * 60)

    extractor = FontPathExtractor(font_path)

    result = extractor.extract_radicals(radicals_and_chars, 'radicals.json')
