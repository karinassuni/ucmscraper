from setuptools import setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='ucmscraper',
    description='Module for scraping UC Merced\'s class schedules',
    long_description=long_description,
    version='2.2.0',
    author='Karina Antonio',
    author_email='karinafantonio@gmail.com',
    url='https://github.com/karinassuni/ucmscraper',
    license='MIT',
    py_modules=['ucmscraper'],
    install_requires=[
        'cssselect',
        'lxml',
        'requests',
    ],
)
