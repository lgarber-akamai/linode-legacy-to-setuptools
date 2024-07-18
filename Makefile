PYTHON ?= python3

.PHONY: format
format: isort black

.PHONY: isort
isort:
	isort .

.PHONY: black
black:
	black .

.PHONY: bake
bake: build
	$(PYTHON) ./legacy_to_techdocs bake

.PHONY: build
build:
	python3 -m build --wheel --sdist

.PHONY: install
install:
	pip install --upgrade -e .[dev]

.PHONY: clean
clean:
	rm -rf ./build ./*.egg-info
