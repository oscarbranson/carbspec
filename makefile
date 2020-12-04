.PHONY: build upload distribute

build:
	python setup.py sdist bdist_wheel

upload:
	twine upload dist/carbspec-$$(python setup.py --version)*

distribute:
	make build
	make upload