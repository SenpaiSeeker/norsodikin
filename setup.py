import re

from setuptools import find_packages, setup

with open("nsdev/__init__.py", encoding="utf-8") as f:
    version = re.findall(r"__version__ = \"(.+)\"", f.read())[0]

with open("requirements.txt", encoding="utf-8") as r:
    requires = [i.strip() for i in r]


setup(
    name="norsodikin",
    version=version,
    description="Library of special mission and encrypted code",
    long_description="A collection of useful tools and utilities.",
    long_description_content_type="text/markdown",
    author="NorSodikin",
    author_email="admin@NorSodikin.com",
    url="https://t.me/NorSodikin",
    license="MIT",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8, <3.13",
    install_requires=requires,
)
