.PHONY: install test demo clean lint format help

# Default target
help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  test       - Run tests"
	@echo "  demo       - Run demo mode"
	@echo "  clean      - Clean up temporary files"
	@echo "  lint       - Run linting"
	@echo "  format     - Format code"
	@echo "  help       - Show this help message"

install:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

test:
	. venv/bin/activate && python test_integration.py

demo:
	. venv/bin/activate && python demo.py

clean:
	rm -rf venv/
	rm -rf __pycache__/
	rm -rf *.pyc
	rm -rf .pytest_cache/

lint:
	. venv/bin/activate && python -m flake8 *.py --max-line-length=120

format:
	. venv/bin/activate && python -m black *.py --line-length=120

# CLI commands
list-issues:
	. venv/bin/activate && python main.py list-issues --repo $(REPO)

scope-issue:
	. venv/bin/activate && python main.py scope-issue --repo $(REPO) --issue-number $(ISSUE)

complete-issue:
	. venv/bin/activate && python main.py complete-issue --repo $(REPO) --issue-number $(ISSUE)

dashboard:
	. venv/bin/activate && python main.py dashboard --repo $(REPO)
