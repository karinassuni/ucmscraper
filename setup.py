from setuptools import setup

setup(
    name='ucmscraper',
    description='Module for scraping UC Merced\'s class schedules',
    version='1.0.0',
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