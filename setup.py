from setuptools import setup, find_packages

setup(
    name="EdxSpider",
    version="0.0.1",
    python_requires='>=3.7',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "requests",
        "requests[socks]",
        "pathvalidate",
        "bs4",
        "lxml"
    ],
    entry_points='''
        [console_scripts]
        edxcli=edxspider.edxcli:edxcli
    ''',
)