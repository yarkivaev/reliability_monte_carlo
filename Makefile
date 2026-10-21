PYTHON ?= python3

.DEFAULT_GOAL := help

.PHONY: help test figure constructor report predefense clean

help:
	@printf '%s\n' \
		'test          run unit tests' \
		'figure        print Monte Carlo estimates for the assignment figure' \
		'constructor   serve the constructor on http://127.0.0.1:8000' \
		'report        open the theoretical report in a browser' \
		'predefense    open the short predefense report in a browser' \
		'clean         remove Python bytecode'

test:
	$(PYTHON) -m unittest discover -s tests

figure:
	$(PYTHON) -m examples.figure

constructor:
	$(PYTHON) -m examples.constructor

report:
	$(PYTHON) -c "from pathlib import Path; import webbrowser; webbrowser.open(Path('project_report.html').resolve().as_uri())"

predefense:
	$(PYTHON) -c "from pathlib import Path; import webbrowser; webbrowser.open(Path('predefense.html').resolve().as_uri())"

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
