SHELL := bash
.ONESHELL:
.DELETE_ON_ERROR:

python = python3
venv_name = venv
activate_venv = . $(venv_name)/bin/activate
format_files = *.py imgtag
lint_files = *.py imgtag

default: lint

clean:
	find imgtag -name __pycache__ -type d -exec rm -rv {} +
	rm -rv .beaker_cache

deps:
	test -d $(venv_name) | $(python) -m venv $(venv_name)
	$(activate_venv)
	pip install --upgrade pip
	pip install -Ur requirements.txt

fmt:
	$(activate_venv)
	isort -rc $(format_files)
	yapf -ir $(format_files)

lint:
	$(activate_venv)
	pylama $(lint_files)
	mypy --ignore-missing-imports $(lint_files)

run:
	$(activate_venv)
	python main.py

test:
	@echo "TODO"
