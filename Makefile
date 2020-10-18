SHELL := bash
.ONESHELL:
.DELETE_ON_ERROR:

python = python3
venv = ./.venv
format_files = *.py imgtag
lint_files = *.py imgtag

venv: $(venv)

$(venv):
	$(python) -m venv $(venv)
	$(venv)/bin/pip install --upgrade pip
	$(venv)/bin/pip install -r requirements.txt

default: run

clean:
	rm -rv $(venv)
	find imgtag -name __pycache__ -type d -exec rm -rv {} +
	rm -rv .beaker_cache

fmt: venv
	$(venv)/bin/isort $(format_files)
	$(venv)/bin/yapf -ir $(format_files)

lint: venv
	$(venv)/bin/pylint $(lint_files)
	$(venv)/bin/mypy --ignore-missing-imports $(lint_files)

run: venv
	$(venv)/bin/python main.py

test: venv
	@echo "TODO"
