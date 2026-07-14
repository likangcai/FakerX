# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/1/1 14:47
# @Software  : PyCharm
# @FileName  : fakerx.py
# -----------------------------
"""
FakerX 主类 - 整合上下文感知、验证、批处理、多格式导出、i18n、模板
"""
import random as _random_module
from typing import Dict, List, Optional, Any, Generator, Union

from faker import Faker

from .schema import SchemaGenerator
from .context import GenerationContext
from .processors import PostProcessor
from .validators import SchemaValidatorEnhanced, generate_pydantic_model
from .batch import BatchGenerator, GenerationCache, MappedWriter
from .anonymizer import DataAnonymizer
from .templates import TemplateRegistry
from .i18n import I18nManager
from .exporters import get_exporter, EXPORTERS
from .exceptions import FakerXError, SchemaError

# ----------------------------------------------------------------
# FakerX 自身定义的方法名集合
# 用于 __getattr__ 中避免与 Faker 方法冲突
# ----------------------------------------------------------------
_FAKERX_OWN_METHODS = frozenset({
    'schema', 'schema_stream', 'schema_chunks', 'schema_parallel',
    'schema_async', 'generate_relations', 'template', 'register_template',
    'load_templates', 'list_templates', 'pydantic', 'anonymize',
    'anonymize_dict', 'anonymize_list', 'export', 'export_stream',
    'to_csv', 'to_json', 'to_excel', 'to_sql', 'to_yaml', 'to_html',
    'to_xml', 'to_parquet', 'to_database', 'switch_locale',
    'generate_localized', 'register_provider', 'register_providers_from_module',
    'validate_schema', 'generate_from_config', 'reset_context',
    'register_processor', 'anonymize_list',
    # 属性
    'context', 'processor',
})


class FakerX(Faker):
    """
    FakerX - 增强版测试数据生成器

    继承自 Faker，完全兼容原生 Faker 的所有方法，同时提供增强功能。
    isinstance(fake, Faker) 返回 True，可作为 Faker 的完全替代品。

    增强功能:
    - fake.schema(...)           结构化生成
    - fake.template('user')      模板生成
    - fake.anonymize(...)        数据脱敏
    - fake.export(data, 'x.csv') 多格式导出
    - fake.schema_parallel(...)  多进程生成
    """

    def __init__(self, locale: str = 'zh_CN', seed: Optional[int] = None):
        # 初始化原生 Faker (继承自 Faker)
        super().__init__(locale)

        # 种子处理
        if seed is not None:
            Faker.seed(seed)

        # 初始化各子系统
        self._context = GenerationContext()
        self._schema_gen = SchemaGenerator(self, context=self._context)
        self._processor = PostProcessor()
        self._validator = SchemaValidatorEnhanced()
        self._templates = TemplateRegistry()
        self._i18n = I18nManager(default_locale=locale)
        self._cache = GenerationCache()
        self._locale = locale

    # ================================================================
    # 兼容性属性
    # ================================================================

    @property
    def _faker(self):
        """返回自身，兼容旧代码中 self._faker 的引用"""
        return self

    # ================================================================
    # unique 代理支持
    # ================================================================

    @property
    def unique(self) -> 'FakerXUniqueProxy':
        """
        返回 unique 代理，与原生 Faker 完全兼容

        Example:
            >>> fake = FakerX()
            >>> fake.unique.name()  # 保证返回唯一的名字
            >>> fake.unique.email() # 保证返回唯一的邮箱
        """
        return FakerXUniqueProxy(self)

    # ================================================================
    # random 属性支持
    # ================================================================

    @property
    def random(self) -> _random_module.Random:
        """返回底层 Faker 的 Random 实例"""
        return super().random

    def __dir__(self):
        """使 dir() 包含 Faker 的方法，增强兼容性"""
        own_attrs = set(object.__dir__(self))
        # 获取 Faker 实例的所有方法（通过代理访问）
        faker_attrs = set(dir(self._factories[0])) if self._factories else set()
        return sorted(own_attrs | faker_attrs)

    # ================================================================
    # seed 类方法支持
    # ================================================================

    @classmethod
    def seed(cls, seed: Optional[int] = None) -> None:
        """
        设置随机种子 (类方法，与 Faker.seed 兼容)

        Example:
            >>> FakerX.seed(42)
            >>> fake1 = FakerX()
            >>> fake2 = FakerX()
            >>> fake1.name() == fake2.name()  # True
        """
        Faker.seed(seed)

    @classmethod
    def seed_instance(cls, instance: 'FakerX', seed: Optional[int] = None) -> None:
        """
        为单个实例设置种子

        Example:
            >>> fake = FakerX()
            >>> FakerX.seed_instance(fake, 42)
        """
        Faker.seed_instance(instance, seed)

    # ================================================================
    # Provider 支持 (继承自 Faker，__getattr__ 自动委托)
    # ================================================================

    # ================================================================
    # Schema 生成 (增强: 上下文 + 后处理 + 验证)
    # ================================================================

    def schema(
            self,
            schema: Dict,
            iterations: int = 1,
            unique_fields: Optional[List[str]] = None,
            foreign_keys: Optional[Dict] = None,
            validate: bool = True,
            post_process: Optional[Dict[str, List[str]]] = None,
    ) -> List[Dict]:
        """生成结构化数据 (增强版)"""
        results = []
        for i in range(iterations):
            self._context.run_hooks('before_record', i)
            record = self._schema_gen.generate(
                schema, 1, unique_fields, foreign_keys
            )[0]

            if post_process:
                record = self._processor.process_record(record, post_process)

            errors = self._validator.validate_record(record, schema)
            if errors:
                raise FakerXError(f"记录 {i} 验证失败: {'; '.join(errors)}")

            self._context.add_record(record)
            self._context.run_hooks('after_record', record, i)
            results.append(record)

        return results

    def schema_stream(
            self,
            schema: Dict,
            iterations: int = 1,
            unique_fields: Optional[List[str]] = None,
            foreign_keys: Optional[Dict] = None,
    ) -> Generator[Dict, None, None]:
        """流式生成"""
        yield from self._schema_gen.generate_stream(
            schema, iterations, unique_fields, foreign_keys
        )

    def schema_chunks(
            self,
            schema: Dict,
            iterations: int = 1,
            chunk_size: int = 1000,
            unique_fields: Optional[List[str]] = None,
            foreign_keys: Optional[Dict] = None,
    ) -> Generator[List[Dict], None, None]:
        """分块生成"""
        yield from self._schema_gen.generate_chunks(
            schema, iterations, chunk_size, unique_fields, foreign_keys
        )

    def generate_relations(self, config: Dict[str, Dict]) -> Dict[str, List[Dict]]:
        """多表关联生成"""
        results = {}
        for table_name, table_config in config.items():
            schema_def = table_config['schema']
            count = table_config['count']
            relations = table_config.get('relations', {})

            foreign_keys = {}
            for fk_field, ref_path in relations.items():
                ref_table, ref_field = ref_path.split('.')
                if ref_table not in results:
                    raise SchemaError(
                        f"关联表 '{ref_table}' 尚未生成，"
                        f"请将 '{ref_table}' 放在 '{table_name}' 之前"
                    )
                ref_values = [row[ref_field] for row in results[ref_table]]
                foreign_keys[fk_field] = (ref_values, ref_field)

            results[table_name] = self.schema(
                schema_def, iterations=count, foreign_keys=foreign_keys
            )
        return results

    # ================================================================
    # 上下文感知
    # ================================================================

    @property
    def context(self) -> GenerationContext:
        return self._context

    def reset_context(self):
        self._context.reset()

    # ================================================================
    # 批处理
    # ================================================================

    def schema_parallel(
            self,
            schema: Dict,
            total_count: int,
            workers: int = 4,
            unique_fields: Optional[List[str]] = None,
    ) -> List[Dict]:
        """多进程并行生成"""
        return BatchGenerator.generate_parallel(
            schema, total_count, workers, unique_fields
        )

    async def schema_async(
            self,
            schema: Dict,
            total_count: int,
            batch_size: int = 100,
    ) -> List[Dict]:
        """异步生成"""
        return await BatchGenerator.generate_async(schema, total_count, batch_size)

    # ================================================================
    # 模板系统
    # ================================================================

    def template(
            self,
            name: str,
            count: int = 1,
            extend: Optional[Dict] = None,
            override: Optional[Dict] = None,
            **kwargs,
    ) -> List[Dict]:
        schema = self._templates.get_schema(name, extend, override)
        return self.schema(schema, iterations=count, **kwargs)

    def register_template(self, name: str, schema: Dict, description: str = ""):
        self._templates.register(name, schema, description)

    def load_templates(self, path: str):
        import os
        if os.path.isfile(path):
            self._templates.load_from_file(path)
        elif os.path.isdir(path):
            self._templates.load_from_directory(path)

    def list_templates(self) -> Dict[str, str]:
        return self._templates.list_templates()

    # ================================================================
    # Pydantic 集成
    # ================================================================

    def pydantic(self, model_class, **overrides):
        """生成 Pydantic 模型数据"""
        return generate_pydantic_model(self._faker, model_class, **overrides)

    # ================================================================
    # 数据脱敏
    # ================================================================

    def anonymize(self, value, field_type='auto'):
        return DataAnonymizer.anonymize(value, field_type)

    def anonymize_dict(self, data: Dict, field_mapping: Dict[str, str]) -> Dict:
        return DataAnonymizer.anonymize_dict(data, field_mapping)

    def anonymize_list(self, data: List[Dict], field_mapping: Dict[str, str]) -> List[Dict]:
        return DataAnonymizer.anonymize_list(data, field_mapping)

    # ================================================================
    # 多格式导出
    # ================================================================

    def export(self, data: List[Dict], filepath: str, format: str = None, **kwargs):
        """智能导出 - 根据文件扩展名自动推断格式"""
        import os
        if format is None:
            ext = os.path.splitext(filepath)[1].lower().strip('.')
            format = ext if ext in EXPORTERS else 'json'
        exporter = get_exporter(format)
        exporter.export(data, filepath, **kwargs)

    def export_stream(self, generator, filepath: str, format: str = None, **kwargs):
        """流式导出"""
        import os
        if format is None:
            ext = os.path.splitext(filepath)[1].lower().strip('.')
            format = ext if ext in EXPORTERS else 'json'
        exporter = get_exporter(format)
        exporter.export_stream(generator, filepath, **kwargs)

    def to_csv(self, data, filepath=None, **kwargs):
        """
        导出 CSV (兼容 v0.2.0)

        旧用法: fake.to_csv(data) -> 返回 CSV 字符串
                fake.to_csv(data, 'file.csv') -> 保存到文件
        新用法: fake.to_csv(data, 'file.csv', **kwargs) -> 保存到文件
        """
        if filepath is None:
            # v0.2.0 兼容: 返回 CSV 字符串
            from io import StringIO
            import csv as _csv
            if not data:
                return ""
            output = StringIO()
            writer = _csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            return output.getvalue()
        get_exporter('csv').export(data, filepath, **kwargs)

    def to_csv_stream(self, generator, filepath, **kwargs):
        """流式导出 CSV"""
        get_exporter('csv').export_stream(generator, filepath, **kwargs)

    def to_json(self, data, filepath=None, **kwargs):
        """
        导出 JSON (兼容 v0.2.0)

        旧用法: fake.to_json(data) -> 返回 JSON 字符串
        新用法: fake.to_json(data, 'file.json', **kwargs) -> 保存到文件
        """
        if filepath is None:
            # v0.2.0 兼容: 返回 JSON 字符串
            import json as _json
            from .exporters.json_ex import DateTimeEncoder
            return _json.dumps(data, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
        get_exporter('json').export(data, filepath, **kwargs)

    def to_excel(self, data, filepath, **kwargs):
        get_exporter('excel').export(data, filepath, **kwargs)

    def to_sql(self, data, filepath, table_name='data', **kwargs):
        get_exporter('sql').export(data, filepath, table_name=table_name, **kwargs)

    def to_yaml(self, data, filepath, **kwargs):
        get_exporter('yaml').export(data, filepath, **kwargs)

    def to_html(self, data, filepath, **kwargs):
        get_exporter('html').export(data, filepath, **kwargs)

    def to_xml(self, data, filepath, **kwargs):
        get_exporter('xml').export(data, filepath, **kwargs)

    def to_parquet(self, data, filepath, **kwargs):
        get_exporter('parquet').export(data, filepath, **kwargs)

    def to_database(self, data, table_name='data', db_path=':memory:', if_exists='replace', **kwargs):
        """
        将数据插入到SQLite数据库（兼容 v0.2.0 签名）

        v0.2.0: fake.to_database(data, 'users', 'test.db', 'replace')
        v2.0.0: fake.to_database(data, 'users', 'test.db')
        """
        import sqlite3
        conn = sqlite3.connect(db_path)
        try:
            if data:
                columns = list(data[0].keys())
                column_defs = ', '.join([f'{col} TEXT' for col in columns])
                create_sql = f'CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})'

                if if_exists == 'replace':
                    conn.execute(f'DROP TABLE IF EXISTS {table_name}')
                    create_sql = f'CREATE TABLE {table_name} ({column_defs})'

                conn.execute(create_sql)

                placeholders = ', '.join(['?' for _ in columns])
                insert_sql = f'INSERT INTO {table_name} ({", ".join(columns)}) VALUES ({placeholders})'

                for row in data:
                    values = [str(row[col]) for col in columns]
                    conn.execute(insert_sql, values)

                conn.commit()
        finally:
            conn.close()

    # ================================================================
    # i18n
    # ================================================================

    def switch_locale(self, locale: str):
        """切换 locale"""
        # 重新初始化 Faker 基类（继承自 Faker）
        super().__init__(locale)
        self._schema_gen = SchemaGenerator(self, context=self._context)
        self._locale = locale

    def generate_localized(self, schema, iterations, locale_weights=None):
        """多 locale 混合生成"""
        return self._i18n.generate_localized(schema, iterations, locale_weights)

    # ================================================================
    # 自定义 Provider
    # ================================================================

    def register_provider(self, name: str, func=None):
        """
        注册自定义数据生成方法 (轻量级)

        支持两种调用方式:
        1. 直接调用: fake.register_provider('phone_cn', gen_func)
        2. 装饰器:  @fake.register_provider('phone_cn')

        Example:
            @fake.register_provider('phone_cn')
            def gen_phone(fake, **kw):
                prefixes = ['138', '139', '150']
                return fake.random_element(prefixes) + ''.join(
                    str(fake.random_digit()) for _ in range(8))
        """

        def _register(fn):
            def wrapper(*args, **kwargs):
                return fn(self._faker, *args, **kwargs)
            setattr(self._faker, name, wrapper)
            return fn

        if func is not None:
            # 直接调用: register_provider('name', func)
            _register(func)
            return func
        else:
            # 装饰器: @register_provider('name')
            return _register

    def register_providers_from_module(self, module):
        """从 Python 模块批量注册 provider"""
        import inspect
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if name.startswith('generate_'):
                provider_name = name.replace('generate_', '')
                self.register_provider(provider_name, obj)

    # ================================================================
    # Schema 验证
    # ================================================================

    def validate_schema(self, schema: Dict, verbose: bool = False) -> bool:
        from .validators import SchemaValidator
        validator = SchemaValidator()
        is_valid = validator.validate(schema)
        if verbose:
            print(validator.report())
        return is_valid

    # ================================================================
    # 后处理器
    # ================================================================

    @property
    def processor(self) -> PostProcessor:
        return self._processor

    def register_processor(self, name: str, func):
        self._processor.register(name, func)

    # ================================================================
    # 配置文件
    # ================================================================

    def generate_from_config(self, config_path: str) -> List[Dict]:
        import os, json
        ext = os.path.splitext(config_path)[1].lower()
        if ext in ('.yaml', '.yml'):
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

        schema = config.get('schema', {})
        iterations = config.get('iterations', 1)
        unique_fields = config.get('unique_fields')
        post_process = config.get('post_process')

        data = self.schema(
            schema, iterations, unique_fields=unique_fields,
            post_process=post_process,
        )

        export_config = config.get('export')
        if export_config:
            self.export(
                data, export_config['filepath'],
                format=export_config.get('format'),
                **{k: v for k, v in export_config.items()
                   if k not in ('filepath', 'format')}
            )
        return data

    # ================================================================
    # FakerX 0.2.0 兼容方法
    # ================================================================

    def uuid4(self) -> str:
        """生成UUID4字符串（兼容 v0.2.0）"""
        import uuid
        return str(uuid.uuid4())

    def custom_url(self, domain: str = None) -> str:
        """生成自定义域名的URL（兼容 v0.2.0）"""
        if domain:
            return f"https://{domain}/{self.slug()}"
        return self.url()

    def validate_email(self, email: str) -> bool:
        """验证邮箱格式（兼容 v0.2.0）"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def set_seed(self, seed_value: int) -> None:
        """设置随机种子（兼容 v0.2.0 的 set_seed 命名）"""
        Faker.seed(seed_value)

    def stats(self, data: List[Dict]) -> Dict[str, Any]:
        """统计生成数据的统计信息（兼容 v0.2.0）"""
        if not data:
            return {}

        stats = {}
        for key in data[0].keys():
            values = [item[key] for item in data]
            if isinstance(values[0], (int, float)):
                stats[key] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values)
                }
            elif isinstance(values[0], str):
                stats[key] = {
                    'count': len(values),
                    'unique': len(set(values)),
                    'avg_length': sum(len(v) for v in values) / len(values)
                }
            else:
                stats[key] = {'count': len(values)}
        return stats

    def load_schema_from_file(self, file_path: str) -> Dict:
        """从JSON或YAML文件加载schema（兼容 v0.2.0）"""
        import os, json
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                import yaml
                return yaml.safe_load(f)
            else:
                return json.load(f)

    def generate_with_validation(self, method: str, validator=None, max_retries: int = 10):
        """生成数据并使用自定义验证器验证（兼容 v0.2.0）"""
        for _ in range(max_retries):
            value = getattr(self, method)()
            if validator is None or validator(value):
                return value
        raise ValueError(
            f"Failed to generate valid value for {method} "
            f"after {max_retries} attempts"
        )

    async def async_batch(self, method: str, iterations: int = 1, unique: bool = False) -> List[Any]:
        """异步批量生成数据（兼容 v0.2.0）"""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        results = []
        seen = set() if unique else None

        for _ in range(iterations):
            value = await loop.run_in_executor(None, getattr(self._faker, method))
            if unique:
                while value in seen:
                    value = await loop.run_in_executor(None, getattr(self._faker, method))
                seen.add(value)
            results.append(value)
        return results

    def nested_schema(self, schema_dict: Dict, iterations: int = 1,
                       unique_fields: List[str] = None) -> List[Dict]:
        """生成嵌套结构的schema数据（兼容 v0.2.0，等价于 schema）"""
        return self.schema(schema_dict, iterations, unique_fields)

    def clean_address(self) -> str:
        """生成不带邮编的地址（兼容 v0.2.0）"""
        import re
        full_address = self.address()
        cleaned = re.sub(r'\s*\d{6}\s*$', '', full_address).strip()
        return cleaned

    def random_date_between(self, start_date: str = '2000-01-01',
                             end_date: str = '2023-12-31') -> str:
        """生成指定日期范围内的随机日期（兼容 v0.2.0）"""
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        random_date = self.date_time_between(start_date=start, end_date=end)
        return random_date.strftime('%Y-%m-%d')

    def batch(self, method: str, iterations: int = 1, unique: bool = False) -> Generator[Any, None, None]:
        """批量生成数据（兼容 v0.2.0，生成器方式）"""
        if not hasattr(self._faker, method):
            raise AttributeError(f"No such method: {method}")
        seen = set() if unique else None
        for _ in range(iterations):
            value = getattr(self._faker, method)()
            if unique:
                while value in seen:
                    value = getattr(self._faker, method)()
                seen.add(value)
            yield value


# ================================================================
# UniqueProxy 兼容实现
# ================================================================

class FakerXUniqueProxy:
    """
    FakerX 的 Unique 代理

    完全兼容原生 Faker 的 unique 机制:
    - fake.unique.name()   -> 返回唯一的 name
    - fake.unique.email()  -> 返回唯一的 email

    同时支持与 Schema 生成器配合:
    - fake.unique 是一个代理对象，调用其上的方法等同于
      调用 faker.unique.{method}()
    """

    def __init__(self, fakerx_instance: 'FakerX'):
        self._fakerx = fakerx_instance
        # 直接使用 Faker 内部的 unique proxy（避免递归）
        self._faker_unique = fakerx_instance._unique_proxy

    def __getattr__(self, name: str) -> Any:
        """
        委托给 Faker 的 unique 代理

        Example:
            fake.unique.name()  ->  self._faker_unique.name()
        """
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return getattr(self._faker_unique, name)
