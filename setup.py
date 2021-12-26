from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

REQUIRES = [
    "click",
    "requests>=2.20.0",
    "tabulate",
    "python-dotenv",
    "pyyaml",
    "jinja2",
]

setup(
    name="evengsdk",
    keywords="evengsdk",
    license="MIT license",
    version="0.2.0",
    author="Tafsir Thiam",
    author_email="ttafsir@gmail.com",
    description=(
        "Python SDK and command line utilities to " "work with the EVE-NG REST API"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ttafsir/evengsdk",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=REQUIRES,
    entry_points={
        "console_scripts": [
            "eve-ng=evengsdk.cli.cli:main",
            "eveng=evengsdk.cli.cli:main",
        ],
    },
)
