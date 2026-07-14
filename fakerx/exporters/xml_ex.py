# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:13
# @Software  : PyCharm
# @FileName  : xml_ex.py
# -----------------------------
"""
XML 导出器
"""
from typing import List, Dict
from .base import BaseExporter
from xml.etree import ElementTree as ET
from xml.dom import minidom


class XMLExporter(BaseExporter):
    """XML 导出器"""

    def export(self, data: List[Dict], filepath: str, root_tag: str = 'data',
               item_tag: str = 'record', **kwargs):
        root = ET.Element(root_tag)

        for record in data:
            item = ET.SubElement(root, item_tag)
            flat = self.flatten(record)
            for key, value in flat.items():
                child = ET.SubElement(item, key.replace(' ', '_'))
                child.text = str(value) if value is not None else ''

        xml_str = ET.tostring(root, encoding='unicode')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent='  ')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)

    def export_stream(self, generator, filepath: str, root_tag: str = 'data',
                      item_tag: str = 'record', **kwargs):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(f'<{root_tag}>\n')

            for record in generator:
                flat = self.flatten(record)
                f.write(f'  <{item_tag}>\n')
                for key, value in flat.items():
                    tag = key.replace(' ', '_')
                    val = str(value) if value is not None else ''
                    # XML 转义
                    val = val.replace('&', '&amp;').replace('<', '&lt;')
                    val = val.replace('>', '&gt;').replace('"', '&quot;')
                    f.write(f'    <{tag}>{val}</{tag}>\n')
                f.write(f'  </{item_tag}>\n')

            f.write(f'</{root_tag}>\n')
