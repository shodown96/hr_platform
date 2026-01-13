"""
# shared-lib/setup.py

from setuptools import setup, find_packages

setup(
    name="hr-shared",
    version="0.1.0",
    description="Shared utilities for HR Platform Microservices",
    author="Your Team",
    author_email="team@company.com",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.5.3",
        "python-jose[cryptography]>=3.3.0",
        "fastapi>=0.109.0",
    ],
    python_requires=">=3.11",
)
"""