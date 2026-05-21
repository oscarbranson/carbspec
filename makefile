.PHONY: build upload distribute

build:
	python -m build

upload:
	twine upload dist/carbspec-$$(python -c 'import carbspec; print(carbspec.__version__)')*

distribute:
	make build
	make upload