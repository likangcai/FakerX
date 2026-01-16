#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FakerX 命令行工具
"""
import argparse
import json
from fakerx import FakerX


def main():
    parser = argparse.ArgumentParser(description='FakerX 数据生成工具')
    parser.add_argument('--locale', default='zh_CN', help='本地化设置')
    parser.add_argument('--method', help='生成方法')
    parser.add_argument('--count', type=int, default=1, help='生成数量')
    parser.add_argument('--schema', help='Schema文件路径')
    parser.add_argument('--output', help='输出文件')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='输出格式')

    args = parser.parse_args()

    fake = FakerX(args.locale)

    if args.schema:
        # 从文件加载schema
        with open(args.schema, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        data = fake.schema(schema, args.count)
    elif args.method:
        # 生成单个方法的数据
        data = list(fake.batch(args.method, args.count))
    else:
        parser.print_help()
        return

    # 输出结果
    if args.output:
        if args.format == 'json':
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            csv_data = fake.to_csv(data)
            with open(args.output, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_data)
        print(f"数据已保存到 {args.output}")
    else:
        if args.format == 'json':
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(fake.to_csv(data))


if __name__ == '__main__':
    main()
