PYTHON ?= python3
PIP ?= pip3

.PHONY: format
format: isort black

.PHONY: isort
isort:
	$(PYTHON) -m isort ./legacy_to_techdocs

.PHONY: black
black:
	$(PYTHON) -m black ./legacy_to_techdocs

.PHONY: bake
bake: build
	$(PYTHON) ./legacy_to_techdocs bake

.PHONY: build
build:
	$(PYTHON) -m build --wheel --sdist

.PHONY: install
install:
	$(PIP) install --upgrade -e .[dev]

.PHONY: clean
clean:
	rm -rf ./build ./*.egg-info
