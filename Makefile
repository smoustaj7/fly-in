run:
	python3 -m src maps/challenger/01_the_impossible_dream.txt

lint:
	flake8 src/*.py
	mypy ./src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
	@rm -rf .mypy_cache

clean:
	rm -rf src/__pycache__
	rm -rf .mypy_cache