PYTHON ?= python

.PHONY: help run test lint

help:
	@echo "Available targets: run test lint"
	@echo "  run  - launch the beat agent demo"
	@echo "  test - execute agent unit tests"
	@echo "  lint - sanity-check Python syntax via py_compile"

run:
	@$(PYTHON) run.py

test:
	@$(PYTHON) -m pytest tests/test_agents.py

lint:
	@$(PYTHON) -m py_compile agents/*.py engine/*.py ui/*.py models.py run.py
