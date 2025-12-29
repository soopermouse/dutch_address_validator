from setuptools import setup, find_packages

setup(
    name="dutch-postal-address",
    version="1.0.0",
    author="Address Validation Team",
    description="Dutch postal address validation and correction",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pydantic>=2.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
        "full": [
            "python-Levenshtein>=0.21.0",
            "rapidfuzz>=3.0.0",
        ]
    },
    python_requires=">=3.11",
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
