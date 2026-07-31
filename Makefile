.PHONY: install execute validate lab

install:
	python -m pip install -r requirements.txt

execute:
	python run_all.py

validate:
	python run_all.py --validate-only

lab:
	jupyter lab
