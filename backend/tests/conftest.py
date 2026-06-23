"""Pytest 全局配置 - 在导入任何模块前设置测试环境变量。"""
import os

# 确保测试使用内存 SQLite，避免产生数据文件副作用
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
