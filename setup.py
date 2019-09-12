from setuptools import setup

setup(
    name='climatepixdb',
    version='0.1',
    packages=['climatepixdb', 'climatepixdb.core'],
    install_requires=[
        'firebase-admin',
        'ujson'
    ],
    url='',
    license='GPL',
    author='notoraptor',
    author_email='',
    description='Script to download images and metadata from ClimatePixWeb database.'
)
