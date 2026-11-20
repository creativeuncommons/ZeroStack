#!/usr/bin/env python3
"""
ZeroStack: Zero-Dependency Enterprise Agent Infrastructure
Setup script for standard packaging compatibility.
"""

import os
from setuptools import setup, find_packages

setup(
    name="creativeuncommons-zerostack",
    version="1.0.0",
    description="Zero-Dependency Enterprise Agent Infrastructure: Sub-millisecond PII Firewall, BM25 Tool Pruning, MCP Server, Durable WAL Loops, and W3C Tracing.",
    long_description=open("README.md", encoding="utf-8").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="CreativeUnCommons Engineering",
    author_email="oss@creativeuncommons.org",
    url="https://github.com/creativeuncommons/ZeroStack",
    license="Apache-2.0",
    python_requires=">=3.10",
    packages=find_packages(include=["zerostack*"]),
    install_requires=[],  # 100% Python Standard Library
    entry_points={
        "console_scripts": [
            "zerostack=zerostack.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
