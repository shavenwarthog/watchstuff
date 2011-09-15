from setuptools import setup, find_packages

setup(
    name='watchstuff',
    packages=find_packages(),
    entry_points = {
        'console_scripts': [
            'watchstuff = watchstuff.watchstuff:main',
            ],
        },
    zip_safe=True,
    install_requires=[
        'distribute',
        'termcolor',
        ],

    author='John Mitchell',
    author_email='johnlmitchell@gmail.com',
    url='http://johntellsall.blogspot.com/',
)

