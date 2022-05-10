from setuptools import setup, find_packages

setup(name="yu_messenger_server",
      version="0.0.3",
      description="Mess Server",
      author="Yuriy Verchenko",
      author_email="yuverch@yandex.ru",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex'],
      scripts=['server/server_run']
      )
