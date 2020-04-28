from setuptools import find_packages, setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='evengsdk',
    version='1.0',
    author='Tafsir Thiam',
    author_email='tafsir.thiam@wwt.com',
    description='EVE-NG SDK for Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=['evengsdk', 'Click'],
    entry_points={
        'console_scripts': [
            'evengcli=evengsdk.cli.cli:main'
        ],
    }
)