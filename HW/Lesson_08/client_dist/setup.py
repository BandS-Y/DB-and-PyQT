from setuptools import setup, find_packages

setup(name="yu_messenger_client",
      version="0.0.2",
      description="Mess Client",
      author="Yuriy Verchenko",
      author_email="yuverch@yandex.ru",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )
