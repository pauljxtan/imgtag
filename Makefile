SHELL :=bash
.ONESHELL:
.DELETE_ON_ERROR:

# Modify according to the name of your virtualenv
activate_venv = . venv/bin/activate
format_files = main.py imgtag
lint_files = main.py imgtag

default: lint

clean:
	find imgtag -name __pycache__ -type d -exec rm -rv {} +
	rm -rv .beaker_cache

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
