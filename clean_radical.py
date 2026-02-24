#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中二病也要造汉字 - 清理工具"""

import json
import re
import os


def clean_path_for_left_component(path_data, max_x, tolerance=20):
    if not path_data:
        return None

    commands = re.findall(r'([MLQCZHV])([^MLQCZHV]*)', path_data.upper())
    cleaned_commands = []
    skip_until_next_M = False

    for cmd, params_str in commands:
        params = [float(x) for x in re.findall(r'-?\d+\.?\d*', params_str)]

        if cmd == 'Z':
            cleaned_commands.append((cmd, ''))
            skip_until_next_M = False
            continue

        if cmd == 'M':
            if len(params) >= 2:
                new_x = params[0]
                if new_x <= max_x + tolerance:
                    cleaned_commands.append((cmd, params_str.strip()))
                    skip_until_next_M = False
                else:
                    skip_until_next_M = True
            continue

        if skip_until_next_M:
            continue

        if cmd in ['L', 'Q', 'C', 'H', 'V']:
            x_coords = [params[i] for i in range(0, len(params), 2)]

            if all(x <= max_x + tolerance for x in x_coords):
                cleaned_commands.append((cmd, params_str.strip()))

    if not cleaned_commands:
        return None

    cleaned_path = ' '.join(f"{cmd} {params}" if params else cmd for cmd, params in cleaned_commands)
    return cleaned_path


def interactive_mode():
    print("\n" + "=" * 60)
    print("🔧 中二病也要造汉字 - 清理工具")
    print("=" * 60)

    print("\n📋 步骤 1: 选择 JSON 文件")
    json_file = input("请输入 JSON 文件路径（默认 radicals.json）：").strip()
    if not json_file:
        json_file = 'radicals.json'

    if not os.path.exists(json_file):
        print(f"❌ 文件不存在：{json_file}")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\n✓ 找到 {len(data)} 个部件：")
    for i, key in enumerate(data.keys(), 1):
        cut_x = data[key].get('cut_x', 'N/A')
        print(f"  {i}. {key} (cut_x: {cut_x})")

    print("\n📋 步骤 2: 选择要清理的部件")
    component_name = input("请输入部件名称（如'手2'）：").strip()

    if component_name not in data:
        print(f"❌ 未找到部件：{component_name}")
        return

    component = data[component_name]
    original_path = component.get('path', '')
    cut_x = component.get('cut_x')

    print(f"\n✓ 部件信息：")
    print(f"  名称：{component_name}")
    print(f"  来源：{component.get('source', 'N/A')}")
    print(f"  建议 cut_x：{cut_x}")
    print(f"  原始路径长度：{len(original_path)} 字符")

    print("\n📋 步骤 3: 设置最大 X 坐标")
    if cut_x:
        print(f"💡 建议值：X = {cut_x}（来自提取时的分割线）")

    max_x_input = input("请输入最大 X 坐标（直接回车使用建议值）：").strip()
    max_x = float(max_x_input) if max_x_input else cut_x

    if max_x is None:
        print("❌ 未提供最大 X 坐标")
        return

    print("\n📋 步骤 4: 执行清理")
    cleaned_path = clean_path_for_left_component(original_path, max_x)

    if not cleaned_path:
        print("❌ 清理后路径为空，请调整 max_x 值")
        return

    print(f"✅ 清理成功！")
    print(f"  原始长度：{len(original_path)} 字符")
    print(f"  清理后：{len(cleaned_path)} 字符")
    print(f"  减少了：{len(original_path) - len(cleaned_path)} 字符")

    print("\n📋 步骤 5: 保存结果")
    output_file = input("请输入输出文件路径（直接回车覆盖原文件）：").strip()
    if not output_file:
        output_file = json_file

    data[component_name]['path'] = cleaned_path
    data[component_name]['note'] = f"从'{component.get('source', 'unknown')}'提取，经路径清理，X<{max_x:.0f}"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✓ 已保存至：{output_file}")

    print("\n📝 清理后路径预览：")
    print(cleaned_path[:300] + "..." if len(cleaned_path) > 300 else cleaned_path)

    print("\n" + "=" * 60)
    print("💡 下一步：")
    print(f"  1. 刷新前端页面")
    print(f"  2. 点击'{component_name}'查看效果")
    print(f"  3. 如果仍有问题，调整 max_x 值重新清理")
    print("=" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='🔧 清理部件路径工具')
    parser.add_argument('json_file', nargs='?', help='JSON 文件路径')
    parser.add_argument('component', nargs='?', help='部件名称')
    parser.add_argument('--max-x', type=float, help='最大 X 坐标')
    parser.add_argument('--output', help='输出文件路径')

    args = parser.parse_args()

    if args.json_file and args.component and args.max_x:
        with open(args.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if args.component not in data:
            print(f"❌ 未找到部件：{args.component}")
            return

        original_path = data[args.component].get('path', '')
        print(f"📊 原始路径长度：{len(original_path)} 字符")

        cleaned_path = clean_path_for_left_component(original_path, args.max_x)

        if cleaned_path:
            print(f"✅ 清理后路径长度：{len(cleaned_path)} 字符")

            data[args.component]['path'] = cleaned_path

            output_file = args.output if args.output else args.json_file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"✓ 已保存至：{output_file}")
        else:
            print("❌ 清理后路径为空")
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
