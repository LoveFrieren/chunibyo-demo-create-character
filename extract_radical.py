#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中二病也要造汉字 - 部件提取工具"""

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import ControlBoundsPen
import json
import os
import re
from pathlib import Path


class SingleRadicalExtractor:
    def __init__(self, font_path):
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"字体文件不存在：{font_path}")

        self.font_path = font_path
        self.font = TTFont(font_path)
        self.glyphSet = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        print(f"✓ 字体加载成功：{os.path.basename(font_path)}")

    def get_char_path(self, char):
        glyph_name = self.cmap.get(ord(char))
        if not glyph_name or glyph_name not in self.glyphSet:
            return None

        glyph = self.glyphSet[glyph_name]
        pen = SVGPathPen(self.glyphSet)
        glyph.draw(pen)
        path_data = pen.getCommands()

        bounds_pen = ControlBoundsPen(self.glyphSet)
        glyph.draw(bounds_pen)
        bounds = bounds_pen.bounds

        return {
            'char': char,
            'glyph_name': glyph_name,
            'path': path_data,
            'bounds': bounds,
            'unicode': f"U+{ord(char):04X}"
        }

    def extract_left_component(self, path_data, bounds, split_x, tolerance=10):
        if not path_data:
            return None

        xMin, yMin, _, yMax = bounds
        commands = re.findall(r'([MLQCZHV])([^MLQCZHV]*)', path_data.upper())

        filtered_commands = []
        last_valid_was_in_range = False

        for cmd, params_str in commands:
            params = [float(x) for x in re.findall(r'-?\d+\.?\d*', params_str)]
            cmd_x_values = [params[i] for i in range(0, len(params), 2)]

            in_range = False
            if cmd == 'Z':
                in_range = last_valid_was_in_range
            elif cmd_x_values:
                for x in cmd_x_values:
                    if xMin - tolerance <= x <= split_x + tolerance:
                        in_range = True
                        break

            if in_range or cmd == 'M':
                filtered_commands.append((cmd, params_str.strip()))
                last_valid_was_in_range = in_range
            elif cmd == 'Z' and last_valid_was_in_range:
                filtered_commands.append((cmd, params_str.strip()))

        if not filtered_commands:
            return None

        cleaned_commands = self._clean_commands(filtered_commands)
        extracted_path = ' '.join(f"{cmd} {params}" if params else cmd for cmd, params in cleaned_commands)
        return extracted_path

    def extract_right_component(self, path_data, bounds, split_x, tolerance=10):
        if not path_data:
            return None

        xMin, yMin, xMax, yMax = bounds
        commands = re.findall(r'([MLQCZHV])([^MLQCZHV]*)', path_data.upper())

        filtered_commands = []
        last_valid_was_in_range = False

        for cmd, params_str in commands:
            params = [float(x) for x in re.findall(r'-?\d+\.?\d*', params_str)]
            cmd_x_values = [params[i] for i in range(0, len(params), 2)]

            in_range = False
            if cmd == 'Z':
                in_range = last_valid_was_in_range
            elif cmd_x_values:
                for x in cmd_x_values:
                    if split_x - tolerance <= x <= xMax + tolerance:
                        in_range = True
                        break

            if in_range or cmd == 'M':
                filtered_commands.append((cmd, params_str.strip()))
                last_valid_was_in_range = in_range
            elif cmd == 'Z' and last_valid_was_in_range:
                filtered_commands.append((cmd, params_str.strip()))

        if not filtered_commands:
            return None

        cleaned_commands = self._clean_commands(filtered_commands)
        extracted_path = ' '.join(f"{cmd} {params}" if params else cmd for cmd, params in cleaned_commands)
        return extracted_path

    def _clean_commands(self, commands):
        cleaned = []
        has_valid_path = False

        for cmd, params in commands:
            if cmd == 'Z':
                if has_valid_path:
                    cleaned.append((cmd, params))
            else:
                if params or cmd in ['M', 'L']:
                    cleaned.append((cmd, params))
                    has_valid_path = True

        if cleaned and cleaned[0][0] != 'M':
            for i, (cmd, params) in enumerate(cleaned):
                if cmd == 'M':
                    cleaned = cleaned[i:]
                    break

        return cleaned

    def _safe_parse_coords(self, path_data):
        if not path_data:
            return [], []

        coords = re.findall(r'-?\d+\.?\d*', path_data)
        x_values = []
        y_values = []

        for i in range(0, len(coords) - 1, 2):
            try:
                x_values.append(float(coords[i]))
                y_values.append(float(coords[i + 1]))
            except (IndexError, ValueError):
                continue

        return x_values, y_values

    def _clean_path_string(self, path_data):
        if not path_data:
            return None

        path_data = re.sub(r'\s+', ' ', path_data).strip()
        path_data = re.sub(r'\s*Z\s*Z\s*', ' Z ', path_data)
        path_data = re.sub(r'^\s*Z\s*', '', path_data)

        return path_data.strip()

    def generate_component_json(self, component_name, component_path, bounds,
                                source_char, cut_x, side, output_file='radicals_new.json'):
        cleaned_path = self._clean_path_string(component_path)

        if cleaned_path:
            x_values, y_values = self._safe_parse_coords(cleaned_path)

            if x_values and y_values:
                actual_bounds = [
                    min(x_values), min(y_values),
                    max(x_values), max(y_values)
                ]
            else:
                actual_bounds = list(bounds)
                print(f"⚠️ 坐标解析失败，使用原边界框")
        else:
            cleaned_path = component_path
            actual_bounds = list(bounds)

        component_data = {
            component_name: {
                "source": f"{source_char}_{side}",
                "cut_x": round(cut_x, 1),
                "bounds": [round(x, 1) for x in actual_bounds],
                "path": cleaned_path,
                "note": f"从'{source_char}'字提取，X{'<' if side == 'left' else '>'}{cut_x:.0f} 部分，建议矢量软件精修"
            }
        }

        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                existing_data.update(component_data)
                output_data = existing_data
            except (json.JSONDecodeError, FileNotFoundError):
                output_data = component_data
        else:
            output_data = component_data

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 部件数据已保存至：{output_file}")
        return component_data

    def extract(self, source_char, side='left', split_x=None,
                component_name=None, output_file='radicals_new.json'):
        """单字提取核心方法"""
        print(f"\n🔍 开始提取：'{source_char}' ({side}侧)")

        char_info = self.get_char_path(source_char)
        if not char_info:
            print(f"❌ 字体中未找到字符：{source_char}")
            return None

        bounds = char_info['bounds']
        print(f"✓ '{source_char}' 边界框：{bounds}")
        print(f"  X 范围：{bounds[0]:.0f} ~ {bounds[2]:.0f}")

        if split_x is None:
            width = bounds[2] - bounds[0]
            split_x = bounds[0] + width * (0.4 if side == 'left' else 0.35)
        print(f"✓ 分割线位置：X = {split_x:.0f}")

        if side == 'left':
            component_path = self.extract_left_component(char_info['path'], bounds, split_x)
        else:
            component_path = self.extract_right_component(char_info['path'], bounds, split_x)

        if not component_path:
            print("❌ 路径提取失败，请调整分割线位置")
            return None

        print(f"✓ 路径提取成功，长度：{len(component_path)} 字符")

        if component_name is None:
            component_name = f"{source_char}_{side}"

        self.generate_component_json(
            component_name=component_name,
            component_path=component_path,
            bounds=bounds,
            source_char=source_char,
            cut_x=split_x,
            side=side,
            output_file=output_file
        )

        return {
            'component_name': component_name,
            'source_char': source_char,
            'side': side,
            'cut_x': split_x,
            'path_length': len(component_path)
        }

    def interactive_mode(self, output_file='radicals_new.json'):
        print("\n" + "=" * 60)
        print("🔤 中二病也要造汉字 - 单字部件提取工具")
        print("=" * 60)

        print("\n📋 步骤 1: 选择源字")
        source_char = input("请输入包含目标部件的汉字（如'持'）：").strip()
        if not source_char:
            print("❌ 输入不能为空")
            return

        print("\n📋 步骤 2: 设置分割参数")
        side = input("提取哪一侧？(left/right，默认 left)：").strip().lower()
        if side not in ['left', 'right']:
            side = 'left'

        char_info = self.get_char_path(source_char)
        if char_info:
            bounds = char_info['bounds']
            width = bounds[2] - bounds[0]
            suggested_split = bounds[0] + width * (0.4 if side == 'left' else 0.35)
            print(f"\n💡 建议分割线位置：X ≈ {suggested_split:.0f}")

        split_x_input = input("请输入分割线 X 坐标（直接回车使用建议值）：").strip()
        split_x = float(split_x_input) if split_x_input else None

        print("\n📋 步骤 3: 命名部件")
        component_name = input("请输入部件名称（如'持_左偏旁'）：").strip()
        if not component_name:
            component_name = None

        print("\n📋 步骤 4: 执行提取")
        result = self.extract(
            source_char=source_char,
            side=side,
            split_x=split_x,
            component_name=component_name,
            output_file=output_file
        )

        if result:
            print("\n" + "=" * 60)
            print("✅ 提取完成！")
            print("=" * 60)
            print(f"部件名称：{result['component_name']}")
            print(f"来源字：{result['source_char']}")
            print(f"切割位置：X = {result['cut_x']:.0f}")
            print(f"路径长度：{result['path_length']} 字符")
            print(f"\n⚠️ 重要提示：")
            print(f"   自动化提取的路径可能存在断裂，建议：")
            print(f"   1. 用 export_char_to_svg.py 导出完整字 SVG")
            print(f"   2. 用 Illustrator/Inkscape 沿分割线手动切割")
            print(f"   3. 复制精修后的路径替换 radicals.json 中的 path")
            print("=" * 60)

    def batch_mode(self, config_list, output_file='radicals_new.json'):
        print("\n" + "=" * 60)
        print("🔤 中二病也要造汉字 - 批量部件提取")
        print("=" * 60)

        results = []
        for config in config_list:
            result = self.extract(
                source_char=config.get('char'),
                side=config.get('side', 'left'),
                split_x=config.get('split_x'),
                component_name=config.get('name'),
                output_file=output_file
            )
            if result:
                results.append(result)

        print(f"\n✅ 批量提取完成！共处理 {len(results)}/{len(config_list)} 个部件")
        return results

    def close(self):
        if hasattr(self, 'font'):
            self.font.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='🔤 中二病也要造汉字 - 单字部件提取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法：
  # 交互式提取（推荐）
  python extract_radical.py

  # 命令行快速提取
  python extract_radical.py 辆 --side left --name 车_左偏旁

  # 指定输出文件
  python extract_radical.py 泊 --side right --name 白_右部件 --output radicals_bai.json
        """
    )

    parser.add_argument('char', nargs='?', help="源汉字（如'辆'）")
    parser.add_argument('--side', choices=['left', 'right'], default='left',
                        help='提取哪一侧（默认：left）')
    parser.add_argument('--name', type=str, help="部件名称（如'车_左偏旁'）")
    parser.add_argument('--split-x', type=float, help='分割线 X 坐标（默认自动计算）')
    parser.add_argument('--output', type=str, default='radicals.json',
                        help='输出文件路径（默认：radicals.json）')
    parser.add_argument('--batch', type=str, help='批量提取配置文件路径')
    parser.add_argument('--font', type=str, default='fonts/NotoSerifSC-VariableFont_wght.ttf',
                        help='字体文件路径')

    args = parser.parse_args()

    current_dir = Path(__file__).parent
    font_path = current_dir / args.font if not os.path.isabs(args.font) else args.font

    try:
        extractor = SingleRadicalExtractor(str(font_path))

        if args.batch:
            batch_path = current_dir / args.batch if not os.path.isabs(args.batch) else args.batch
            with open(batch_path, 'r', encoding='utf-8') as f:
                config_list = json.load(f)
            extractor.batch_mode(config_list, args.output)
        elif args.char:
            extractor.extract(
                source_char=args.char,
                side=args.side,
                split_x=args.split_x,
                component_name=args.name,
                output_file=args.output
            )
        else:
            extractor.interactive_mode(args.output)

    except FileNotFoundError as e:
        print(f"❌ 错误：{e}")
        import sys
        sys.exit(1)

    except Exception as e:
        print(f"❌ 运行时错误：{e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)

    finally:
        if 'extractor' in locals():
            extractor.close()


if __name__ == "__main__":
    main()
