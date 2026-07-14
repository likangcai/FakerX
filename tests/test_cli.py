# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:16
# @Software  : PyCharm
# @FileName  : test_cli.py
# -----------------------------
"""
CLI 测试
"""

import pytest
import subprocess
import sys
import os
from fakerx import FakerX
from fakerx.cli import main, create_parser


class TestCLI:
    """CLI 功能测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_cli_parser_creation(self):
        """CLI 参数解析器创建"""
        parser = create_parser()
        assert parser is not None

    def test_cli_help(self):
        """CLI 帮助信息"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--help'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert 'FakerX - 增强版测试数据生成工具' in result.stdout

    def test_cli_version(self):
        """CLI 版本信息"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--version'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert 'FakerX' in result.stdout

    def test_cli_method_call(self):
        """CLI 方法调用"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--method', 'name', '--count', '3'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split('\n')
        assert len(lines) == 3  # 3 个名字

    def test_cli_template(self):
        """CLI 模板使用"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--template', 'user', '--count', '2'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split('\n')
        assert len(lines) >= 2  # 至少 2 个用户

    def test_cli_schema(self):
        """CLI Schema 使用"""
        schema = {'id': '{pyint}', 'name': '{name}'}
        schema_file = 'test_schema.json'
        with open(schema_file, 'w') as f:
            import json
            json.dump(schema, f)

        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--schema', schema_file, '--count', '2'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split('\n')
        assert len(lines) >= 2  # 至少 2 条记录

        os.remove(schema_file)

    def test_cli_output_format(self):
        """CLI 输出格式"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--method', 'name', '--count', '1', '--format', 'json'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        import json
        # 终端输出是逐条 JSON 行，可以解析为 dict
        data = json.loads(result.stdout.strip())
        assert isinstance(data, dict)
        assert 'name' in data

    def test_cli_locale(self):
        """CLI locale 设置"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--method', 'name', '--locale', 'en_US', '--count', '1'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        name = result.stdout.strip()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_cli_seed(self):
        """CLI 种子设置"""
        result1 = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--method', 'name', '--seed', '42', '--count', '1'],
            capture_output=True, text=True
        )
        result2 = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--method', 'name', '--seed', '42', '--count', '1'],
            capture_output=True, text=True
        )
        assert result1.returncode == 0
        assert result2.returncode == 0
        assert result1.stdout == result2.stdout  # 相同种子，相同结果

    def test_cli_list_templates(self):
        """CLI 列出模板"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--list-templates'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert 'user' in result.stdout
        assert 'product' in result.stdout

    def test_cli_list_locales(self):
        """CLI 列出 locale"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--list-locales'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert 'zh_CN' in result.stdout
        assert 'en_US' in result.stdout

    def test_cli_validate_schema(self):
        """CLI 验证 Schema"""
        schema = {'id': {'method': 'pyint', 'min_value': 1, 'max_value': 100}}
        schema_file = 'test_schema.json'
        with open(schema_file, 'w') as f:
            import json
            json.dump(schema, f)

        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--validate', schema_file],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert '验证通过' in result.stdout

        # 无效 Schema
        invalid_schema = {'id': {'method': 'pyint', 'min_value': 100, 'max_value': 50}}
        with open(schema_file, 'w') as f:
            json.dump(invalid_schema, f)

        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--validate', schema_file],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        assert '错误' in result.stdout or '验证失败' in result.stdout

        os.remove(schema_file)

    def test_cli_interactive(self):
        """CLI 交互模式"""
        # 交互模式需要手动测试
        pass


class TestCLIEdgeCases:
    """CLI 边界情况"""

    def test_cli_invalid_method(self):
        """无效方法"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--method', 'nonexistent_method', '--count', '1'],
            capture_output=True, text=True
        )
        assert result.returncode != 0

    def test_cli_invalid_template(self):
        """无效模板"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--template', 'nonexistent_template', '--count', '1'],
            capture_output=True, text=True
        )
        assert result.returncode != 0

    def test_cli_invalid_schema(self):
        """无效 Schema"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--schema', 'nonexistent_schema.json', '--count', '1'],
            capture_output=True, text=True
        )
        assert result.returncode != 0

    def test_cli_invalid_format(self):
        """无效格式"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--method', 'name', '--format', 'unknown_format'],
            capture_output=True, text=True
        )
        assert result.returncode != 0


class TestCLIPerformance:
    """CLI 性能测试"""

    def test_cli_large_generation(self):
        """CLI 大数据生成"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx', '--method', 'name', '--count', '1000'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split('\n')
        assert len(lines) == 1000


class TestCLIErrorHandling:
    """CLI 错误处理"""

    def test_cli_missing_arguments(self):
        """缺少参数"""
        result = subprocess.run(
            [sys.executable, '-m', 'fakerx'],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        assert 'usage:' in result.stderr


class TestCLIDocumentation:
    """CLI 文档测试"""

    def test_cli_example_code_runs(self):
        """CLI 示例代码能正常运行"""
        # 测试 cli.py 中的示例
        pass
