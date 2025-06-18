"""NexusChat package setup."""

from setuptools import setup, find_packages

setup(
    name="nexuschat",
    version="1.0.0",
    description="ChatGPT-like interface for local and cloud AI models",
    author="Abhi",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.115",
        "uvicorn[standard]>=0.34",
        "python-dotenv>=1.0",
        "httpx>=0.28",
        "aiosqlite>=0.20",
        "jinja2>=3.1",
        "python-multipart>=0.0.20",
        "pydantic>=2.10",
        "pydantic-settings>=2.7",
        "passlib[bcrypt]>=1.7",
        "python-jose[cryptography]>=3.3",
        "markdown>=3.7",
        "pygments>=2.18",
        "sse-starlette>=2.2",
    ],
    entry_points={
        "console_scripts": [
            "nexuschat=main:main",
        ],
    },
)
