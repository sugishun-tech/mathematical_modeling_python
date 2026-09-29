.PHONY: test execute validate audit html visual

test:
	python -m pytest -q

execute:
	python run_all.py

validate:
	python run_all.py --validate-only

audit:
	python scripts/audit_project.py

html:
	python scripts/export_html.py

visual:
	python scripts/verify_rendering.py
