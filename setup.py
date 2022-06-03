from setuptools import setup, find_packages

setup(
	name='src',
	version='1.0',
	packages=find_packages(),
	author='Vlad Zverev',
	description='',
	install_requires=[
		'requests==2.27.1',
		'SQLAlchemy==1.4.36',
		'Flask==2.1.2',
		'base58==2.1.1',
		'ecdsa==0.17.0',
	]
)
