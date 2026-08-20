.PHONY: bootstrap run test check
bootstrap:
	python scripts/bootstrap_demo.py
run:
	uvicorn app.main:app --reload
test:
	pytest
check:
	python -m compileall -q app ml scripts tests
	pytest
