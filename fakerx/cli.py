# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:14
# @Software  : PyCharm
# @FileName  : cli.py
# -----------------------------
"""
增强 CLI - 交互模式、模板预览、Schema 验证、DB 导入导出
"""

import argparse
import json
import sys
import os
from typing import Optional


def create_parser() -> argparse.ArgumentParser:
    """创建 CLI 参数解析器"""
    parser = argparse.ArgumentParser(
        prog='fakerx',
        description='FakerX - 增强版测试数据生成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成 10 个用户名
  fakerx --method user_name --count 10

  # 使用模板生成数据
  fakerx --template user --count 100 --output users.csv

  # 从 Schema JSON 生成
  fakerx --schema user_schema.json --count 50 --format excel --output users.xlsx

  # 列出所有模板
  fakerx --list-templates

  # 列出所有支持的 locale
  fakerx --list-locales

  # 验证 Schema
  fakerx --validate schema.json

  # 交互模式
  fakerx --interactive
        """,
    )

    # 基本参数
    parser.add_argument('--method', '-m', type=str,
                        help='要调用的 faker 方法名 (如: name, email, phone_number)')
    parser.add_argument('--count', '-n', type=int, default=1,
                        help='生成数据条数 (默认: 1)')

    # Schema 和模板
    parser.add_argument('--schema', '-s', type=str,
                        help='Schema JSON 文件路径')
    parser.add_argument('--template', '-t', type=str,
                        help='使用预设模板 (如: user, product, order)')
    parser.add_argument('--list-templates', action='store_true',
                        help='列出所有可用模板')
    parser.add_argument('--list-locales', action='store_true',
                        help='列出所有支持的 locale')

    # 输出
    parser.add_argument('--output', '-o', type=str,
                        help='输出文件路径 (不指定则输出到终端)')
    parser.add_argument('--format', '-f', type=str, default='json',
                        choices=['csv', 'json', 'jsonl', 'excel', 'xlsx',
                                 'sql', 'sqlite', 'yaml', 'html', 'xml',
                                 'parquet'],
                        help='输出格式 (默认: json)')

    # Locale 和随机种子
    parser.add_argument('--locale', '-l', type=str, default='zh_CN',
                        help='Locale (默认: zh_CN)')
    parser.add_argument('--seed', type=int, default=None,
                        help='随机种子 (固定种子可复现数据)')

    # 验证
    parser.add_argument('--validate', '-v', type=str,
                        help='验证 Schema 文件 (不生成数据)')

    # 交互模式
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='交互式模式')

    # 并行
    parser.add_argument('--workers', '-w', type=int, default=1,
                        help='并行进程数 (默认: 1)')
    parser.add_argument('--stream', action='store_true',
                        help='流式生成 (大数据量时节省内存)')

    # 唯一性
    parser.add_argument('--unique', '-u', type=str, nargs='*',
                        help='需要唯一的字段列表')

    # 静默
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='静默模式 (不输出额外信息)')

    # 版本
    parser.add_argument('--version', action='store_true',
                        help='显示版本信息')

    # 数据脱敏
    parser.add_argument('--anonymize', type=str, nargs=2,
                        metavar=('VALUE', 'TYPE'),
                        help='脱敏数据，如: --anonymize 13812345678 phone')

    # 数据统计
    parser.add_argument('--stats', action='store_true',
                        help='统计生成数据的统计信息')

    # 带验证的数据生成
    parser.add_argument('--generate-with-validation', type=str, nargs='+',
                        metavar=('METHOD', 'KEYWORD'),
                        help='带验证的数据生成，如: --generate-with-validation email test')

    # 从配置文件生成
    parser.add_argument('--generate-from-config', type=str,
                        metavar='CONFIG_PATH',
                        help='从配置文件生成数据，支持 YAML/JSON')

    return parser


def cmd_list_templates(fake, args):
    """列出所有模板"""
    templates = fake.list_templates()
    print(f"\n{'名称':<15} {'描述'}")
    print("-" * 50)
    for name, desc in templates.items():
        print(f"{name:<15} {desc}")
    print(f"\n共 {len(templates)} 个模板")


def cmd_list_locales():
    """列出所有 locale"""
    from fakerx.i18n import SUPPORTED_LOCALES
    print(f"\n{'Locale':<10} {'名称'}")
    print("-" * 30)
    for code, name in SUPPORTED_LOCALES.items():
        print(f"{code:<10} {name}")
    print(f"\n共 {len(SUPPORTED_LOCALES)} 个 locale")


def cmd_validate(schema_path: str):
    """验证 Schema 文件"""
    from fakerx import FakerX

    with open(schema_path, 'r', encoding='utf-8') as f:
        if schema_path.endswith('.yaml') or schema_path.endswith('.yml'):
            import yaml
            schema = yaml.safe_load(f)
        else:
            schema = json.load(f)

    fake = FakerX()
    is_valid = fake.validate_schema(schema, verbose=True)
    return 0 if is_valid else 1


def cmd_interactive():
    """交互式模式"""
    from fakerx import FakerX
    fake = FakerX()

    print("=" * 50)
    print("  FakerX 交互模式")
    print("  输入 'help' 查看帮助, 'quit' 退出")
    print("=" * 50)

    while True:
        try:
            cmd = input("\nfakerx> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if not cmd:
            continue
        if cmd in ('quit', 'exit', 'q'):
            print("再见!")
            break
        if cmd == 'help':
            print("""
命令:
  method <name> [count]    调用 faker 方法
  template <name> [count]  使用模板生成
  schema <json>            从 JSON 字符串生成
  list templates           列出模板
  list locales             列出 locale
  locale <code>            切换 locale
  quit                     退出
            """)
            continue

        parts = cmd.split()
        action = parts[0]

        if action == 'method' and len(parts) >= 2:
            method_name = parts[1]
            count = int(parts[2]) if len(parts) >= 3 else 1
            for _ in range(count):
                method = getattr(fake, method_name, None)
                if method:
                    print(method())
                else:
                    print(f"未知方法: {method_name}")
                    break

        elif action == 'template' and len(parts) >= 2:
            name = parts[1]
            count = int(parts[2]) if len(parts) >= 3 else 1
            try:
                data = fake.template(name, count=count)
                for record in data:
                    print(json.dumps(record, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"错误: {e}")

        elif action == 'list' and len(parts) >= 2:
            if parts[1] == 'templates':
                cmd_list_templates(fake, None)
            elif parts[1] == 'locales':
                cmd_list_locales()

        elif action == 'locale' and len(parts) >= 2:
            # 需要 i18n 支持
            print(f"Locale 切换需要重新初始化。请使用: fakerx --locale {parts[1]} ...")

        else:
            print(f"未知命令: {cmd}. 输入 'help' 查看帮助。")


def main(argv: Optional[list] = None) -> int:
    """CLI 主入口"""
    parser = create_parser()
    args = parser.parse_args(argv)

    # 处理版本
    if args.version:
        from fakerx import __version__
        print(f"FakerX {__version__}")
        return 0

    # 处理特殊命令
    if args.list_locales:
        cmd_list_locales()
        return 0

    if args.interactive:
        cmd_interactive()
        return 0

    if args.validate:
        return cmd_validate(args.validate)

    from fakerx import FakerX
    from faker import Faker

    # 初始化
    fake = FakerX(args.locale)
    if args.seed is not None:
        Faker.seed(args.seed)

    if args.list_templates:
        cmd_list_templates(fake, args)
        return 0

    # 处理脱敏
    if args.anonymize:
        value, field_type = args.anonymize
        result = fake.anonymize(value, field_type)
        print(result)
        return 0

    # 处理统计
    if args.stats:
        # 需要先有数据才能统计
        pass  # 在生成数据后处理

    # 处理带验证的数据生成
    if args.generate_with_validation:
        method = args.generate_with_validation[0]
        keyword = args.generate_with_validation[1] if len(args.generate_with_validation) > 1 else None
        if keyword:
            result = fake.generate_with_validation(method, lambda x: keyword not in x)
        else:
            result = fake.generate_with_validation(method)
        print(result)
        return 0

    # 从配置文件生成
    if args.generate_from_config:
        data = fake.generate_from_config(args.generate_from_config)
        # 输出
        if args.output:
            from fakerx.exporters import get_exporter
            exporter = get_exporter(args.format)
            exporter.export(data, args.output)
            if not args.quiet:
                print(f"✅ 已生成 {len(data)} 条数据 -> {args.output} ({args.format})")
        else:
            for record in data:
                print(json.dumps(record, ensure_ascii=False, default=str))
        return 0

    # 生成数据
    data = None
    generator = None

    # 方式1: 单方法调用
    if args.method:
        if args.stream and args.count > 1000:
            def gen():
                for _ in range(args.count):
                    method = getattr(fake, args.method)
                    yield {args.method: method()}

            generator = gen()
        else:
            data = []
            for _ in range(args.count):
                method = getattr(fake, args.method)
                data.append({args.method: method()})

    # 方式2: 模板
    elif args.template:
        if args.stream and args.count > 1000:
            generator = fake.schema_stream(
                fake._templates.get_schema(args.template),
                iterations=args.count,
                unique_fields=args.unique,
            )
        else:
            data = fake.template(
                args.template, count=args.count,
                unique_fields=args.unique,
            )

    # 方式3: Schema 文件
    elif args.schema:
        with open(args.schema, 'r', encoding='utf-8') as f:
            if args.schema.endswith('.yaml') or args.schema.endswith('.yml'):
                import yaml
                schema = yaml.safe_load(f)
            else:
                schema = json.load(f)

        if args.workers > 1:
            # 多进程并行
            from fakerx.batch import BatchGenerator
            data = BatchGenerator.generate_parallel(
                schema, args.count,
                workers=args.workers,
                unique_fields=args.unique,
            )
        elif args.stream and args.count > 1000:
            generator = fake.schema_stream(
                schema, iterations=args.count,
                unique_fields=args.unique,
            )
        else:
            data = fake.schema(
                schema, iterations=args.count,
                unique_fields=args.unique,
            )

    else:
        parser.print_help(file=sys.stderr)
        return 1

    # 输出
    if args.output:
        from fakerx.exporters import get_exporter

        exporter = get_exporter(args.format)

        if generator is not None:
            exporter.export_stream(generator, args.output)
        else:
            exporter.export(data, args.output)

        if not args.quiet:
            count = args.count
            print(f"✅ 已生成 {count} 条数据 -> {args.output} ({args.format})")
    else:
            # 输出到终端
            if generator is not None:
                for i, record in enumerate(generator):
                    if i >= args.count:
                        break
                    print(json.dumps(record, ensure_ascii=False, default=str))
            elif data:
                for i, record in enumerate(data):
                    if i >= args.count:
                        break
                    print(json.dumps(record, ensure_ascii=False, default=str))

    return 0


if __name__ == '__main__':
    sys.exit(main())
