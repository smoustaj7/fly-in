all:
	python3 -m src.main


lint:
	flake8 src/*.py
	mypy --check-untyped-defs src/*.py
	@rm -rf .mypy_cache

clean:
	rm -rf src/__pycache__
	rm -rf .mypy_cache