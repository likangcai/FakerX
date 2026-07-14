# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:16
# @Software  : PyCharm
# @FileName  : test_exporters.py
# -----------------------------
"""
导出器测试
"""
import json
import pytest
import os
import tempfile
from fakerx import FakerX
from fakerx.exporters import (
    get_exporter, EXPORTERS,
    CSVExporter, JSONExporter, ExcelExporter,
    SQLExporter, YAMLExporter, HTMLExporter,
    XMLExporter, ParquetExporter,
)


class TestExporters:
    """导出器功能测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)
        self.data = self.fake.template('user', count=5)

    def test_csv_exporter(self):
        """CSV 导出器"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as f:
            filepath = f.name

        CSVExporter().export(self.data, filepath)
        assert os.path.exists(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 6  # header + 5 data rows
            assert 'id' in lines[0]
            assert 'username' in lines[0]

    def test_json_exporter(self):
        """JSON 导出器"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            filepath = f.name

        JSONExporter().export(self.data, filepath)
        assert os.path.exists(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert len(data) == 5
            assert 'email' in data[0]

    def test_jsonl_exporter(self):
        """JSONL 导出器"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            filepath = f.name

        JSONExporter().to_jsonl(self.data, filepath)
        assert os.path.exists(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 5
            for line in lines:
                json.loads(line)

    def test_sql_exporter(self):
        """SQL 导出器"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as f:
            filepath = f.name

        SQLExporter().export(self.data, filepath, table_name='users')
        assert os.path.exists(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'INSERT INTO' in content
            assert 'users' in content

    def test_yaml_exporter(self):
        """YAML 导出器"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as f:
            filepath = f.name

        YAMLExporter().export(self.data, filepath)
        assert os.path.exists(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'username:' in content

    def test_html_exporter(self):
        """HTML 导出器"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
            filepath = f.name

        HTMLExporter().export(self.data, filepath, title='用户列表')
        assert os.path.exists(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '<table>' in content
            assert '用户列表' in content

    def test_xml_exporter(self):
        """XML 导出器"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as f:
            filepath = f.name

        XMLExporter().export(self.data, filepath, root_tag='users', item_tag='user')
        assert os.path.exists(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '<users>' in content
            assert '<user>' in content

    def test_excel_exporter(self):
        """Excel 导出器"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as f:
            filepath = f.name

        try:
            ExcelExporter().export(self.data, filepath)
            assert os.path.exists(filepath)
        except ImportError:
            pytest.skip("openpyxl 未安装")

    def test_parquet_exporter(self):
        """Parquet 导出器"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as f:
            filepath = f.name

        try:
            ParquetExporter().export(self.data, filepath)
            assert os.path.exists(filepath)
        except ImportError:
            pytest.skip("pyarrow 未安装")

    def test_exporter_registry(self):
        """导出器注册表"""
        exporter = get_exporter('csv')
        assert isinstance(exporter, CSVExporter)

        exporter = get_exporter('json')
        assert isinstance(exporter, JSONExporter)

        with pytest.raises(ValueError):
            get_exporter('unknown_format')

    def test_stream_export(self):
        """流式导出"""
        def data_generator():
            for record in self.data:
                yield record

        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as f:
            filepath = f.name

        CSVExporter().export_stream(data_generator(), filepath)
        assert os.path.exists(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 6  # header + 5 data rows
