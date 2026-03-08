PYTHON ?= python

.PHONY: help run run-server test lint

help:
	@echo "Available targets: run run-server test lint"
	@echo "  run        - launch the beat agent demo (Rich UI or headless)"
	@echo "  run-server - launch the FastAPI/WebSocket HUD service"
	@echo "  test       - execute pytest test suites"
	@echo "  lint       - sanity-check Python syntax via py_compile"

run:
	@$(PYTHON) run.py

run-server:
	@$(PYTHON) -m uvicorn new_app.server:app --host 0.0.0.0 --port 8000

test:
	@$(PYTHON) -m pytest tests

lint:
	@$(PYTHON) -m py_compile agents/*.py engine/*.py ui/*.py models.py run.py server.py backend/*.py tests/*.py
