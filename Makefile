# -*- MakeFile -*-

VERSION = $(shell grep "__version__" ltapy/__init__.py | cut -d " " -f 3)

clean:
	find . -type f -name '*.py[co]' -exec rm -f {} +
	find . -type d -name '__pycache__' -exec rm -rf {} +
	rm -rf ltapy.egg-info

link: clean
	python setup.py develop

unlink:
	python setup.py develop --uninstall

build: clean
	python setup.py sdist

install:
	pip install dist/ltapy-$(VERSION).zip

uninstall:
	pip uninstall ltapy
