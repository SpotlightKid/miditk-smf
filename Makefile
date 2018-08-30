BROWSER ?= xdg-open
PYTHON_PACKAGE = miditk
TESTS_PACKAGE = tests
PYTHON ?= python

.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help

help:
	@echo "Available Makefile targets:"
	@echo
	@echo "dist           builds source and wheel package"
	@echo "install        install the package to the active Python environment"
	@echo "docs           generate Sphinx HTML documentation, including API docs"
	@echo "test           run tests on every Python version with tox"
	@echo "flake8         run style checks and static analysis with flake8"
	@echo "pylint         run style checks and static analysis with pylint"
	@echo "docstrings     check docstring presence and style conventions with pydocstyle"
	@echo "coverage       check code coverage with the default Python version"
	@echo "metrics        print code metrics with radon"
	@echo "clean          remove all build, test, coverage and Python artifacts"
	@echo "clean-build    remove Python file artifacts"
	@echo "clean-pyc      remove Python file artifacts"

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr reports/

test: ## run tests on every Python version with tox
	tox

pylint: ## run style checks and static analysis with pylint
	@-mkdir -p reports/
	@-pylint --output-format=colorized $(PYTHON_PACKAGE) $(TESTS_PACKAGE)

flake8: ## run style checks and static analysis with flake8
	flake8 $(PYTHON_PACKAGE) $(TESTS_PACKAGE)

docstrings: ## check docstring presence and style conventions with pydocstyle
	pydocstyle $(PYTHON_PACKAGE)

lint: flake8 docstrings pylint

coverage: ## check code coverage quickly with the default Python
	@-mkdir -p reports/coverage
	coverage run --source $(PYTHON_PACKAGE) `which py.test`
	coverage report -m
	@coverage html -d reports/coverage
	@$(BROWSER) reports/coverage/index.html

metrics: ## print code metrics with radon
	radon raw -s $(PYTHON_PACKAGE) $(TEST_PACKAGE)
	radon cc -s $(PYTHON_PACKAGE) $(TEST_PACKAGE)
	radon mi -s $(PYTHON_PACKAGE) $(TEST_PACKAGE)

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/$(PYTHON_PACKAGE).rst
	sphinx-apidoc --no-toc -o docs/ $(PYTHON_PACKAGE)
	@mkdir -p docs/_static
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

release: dist ## package and upload a release
	twine upload --skip-existing dist/*.whl dist/*.tar.gz

dist: clean docs ## builds source and wheel package
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	$(PYTHON) setup.py install
