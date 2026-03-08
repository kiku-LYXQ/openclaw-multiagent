.PHONY: all help run test lint
.DEFAULT_GOAL := help

help:
	@echo "Usage: make [run|test|lint]"
	@echo "Targets reference new-app/DESIGN_DOC.md for BPM/agent contracts and INTERFACES.md for expected behaviors."

run:
	@echo "Simulating run: consult new-app/DESIGN_DOC.md §2 & §4 for agent + beat engine orchestration."
	@echo "Intended behavior: heartbeat at BPM, dispatch RhythmEvent payloads, render CLI HUD via ui/console.py."

test:
	@echo "Simulating tests: ensure agent.tick/input/state outputs match INTERFACES.md tables."
	@echo "Reference: new-app/DESIGN_DOC.md §4 测试流程建议。"

lint:
	@echo "Simulating lint: run ruff/flake8 on agents/, engine/, ui/ as per design doc style notes."
	@echo "Third-party modules: rich, dataclasses."
