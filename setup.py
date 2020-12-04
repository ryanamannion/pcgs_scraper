import setuptools
import pcgs_scraper

with open("README.md", "r") as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = f.read().split('\n')

setuptools.setup(
    name="pcgs_scraper",
    version=pcgs_scraper.__version__,
    author="Ryan A. Mannion",
    author_email="ram321@georgetown.edu",
    description="tools for scraping coin data from pcgs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['pcgs_scraper'],
    python_requires='>=3.7',
    install_requires=requirements
)