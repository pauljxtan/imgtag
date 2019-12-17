SHELL :=bash
.ONESHELL:
.DELETE_ON_ERROR:

# Modify according to the name of your virtualenv
activate_venv = . venv/bin/activate

default: lint

clean:
	fd -I __pycache__ imgtag -x rm -rfv {}
	rm -rfv .beaker_cache

lint:
	$(activate_venv)
	isort -df -rc -w 99 imgtag
	yapf -dr main.py imgtag
	pylama imgtag
	mypy --ignore-missing-imports imgtag

run:
	$(activate_venv)
	python main.py

test:
	@echo "TODO"
