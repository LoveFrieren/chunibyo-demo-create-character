#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中二病也要造汉字 - 部件手动添加工具"""

import json
import re
import os
from pathlib import Path


def format_path(path_input):
    if not path_input:
        return None

    fixed = path_input.replace('\n', ' ').replace('\r', ' ')

    fixed = fixed.replace(',', ' ')

    fixed = re.sub(r'\s+', ' ', fixed).strip()

    return fixed


def add_radical_interactive(json_file='radicals.json'):
    print("\n" + "=" * 70)
    print("🔤 中二病也要造汉字 - 部件手动添加工具")
    print("=" * 70)

    if not os.path.exists(json_file):
        print(f"\n⚠️  {json_file} 不存在，将创建新文件")
        existing_data = {}
    else:
        with open(json_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        print(f"\n✓ 已加载 {len(existing_data)} 个现有部件")

    while True:
        print("\n" + "-" * 70)
        print("📋 添加新部件（输入 q 退出）")
        print("-" * 70)

        name = input("\n① 部件名称（如'冰 2'）：").strip()
        if name.lower() == 'q':
            break
        if not name:
            print("❌ 名称不能为空")
            continue

        source = input("② source（如'冯_left_manual'）：").strip()
        if not source:
            print("❌ source 不能为空")
            continue

        print("\n③ 输入 path 数据（Inkscape 复制的 d 属性）：")
        print("   提示：直接粘贴多行内容，输入空行结束")
        path_lines = []
        while True:
            line = input()
            if line == '':
                break
            path_lines.append(line)

        path_raw = '\n'.join(path_lines)
        path_formatted = format_path(path_raw)

        if not path_formatted:
            print("❌ path 不能为空")
            continue

        print(f"\n✓ 格式化后路径长度：{len(path_formatted)} 字符")
        print(f"  预览：{path_formatted[:100]}...")

        note = input("\n④ note 说明（可选，直接回车跳过）：").strip()

        scaleY_input = input("⑤ scaleY（手动提取输 0.2，自动提取回车默认 -0.2）：").strip()
        if scaleY_input:
            try:
                scaleY = float(scaleY_input)
            except ValueError:
                print("⚠️  无效数值，使用默认值 -0.2")
                scaleY = -0.2
        else:
            scaleY = -0.2

        component = {
            "source": source,
            "path": path_formatted
        }

        if note:
            component["note"] = note

        if scaleY != -0.2:
            component["scaleY"] = scaleY

        existing_data[name] = component

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 已添加 '{name}' 到 {json_file}")
        print(f"  source: {source}")
        print(f"  path 长度：{len(path_formatted)}")
        if note:
            print(f"  note: {note}")
        print(f"  scaleY: {scaleY}")

        cont = input("\n继续添加？(y/n，默认 y)：").strip().lower()
        if cont == 'n':
            break

    print(f"\n👋 完成！共 {len(existing_data)} 个部件")
    print(f"📁 文件：{Path(json_file).absolute()}")
    print(f"\n💡 下一步：刷新前端页面验证效果")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='🔤 交互式部件添加工具')
    parser.add_argument('--json', default='radicals.json', help='JSON 文件路径')

    args = parser.parse_args()
    add_radical_interactive(args.json)
