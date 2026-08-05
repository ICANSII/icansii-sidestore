.PHONY: install serve test validate validate-releases build clean

PYTHON := .venv/bin/python
MKDOCS := .venv/bin/mkdocs

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install --requirement requirements-docs.txt

serve:
	$(MKDOCS) serve

test:
	$(PYTHON) -m unittest discover --start-directory tests --verbose

validate: test
	$(PYTHON) scripts/validate_source.py apps.json \
		--repository ICANSII/icansii-sidestore
	$(MKDOCS) build --strict --site-dir site

validate-releases: test
	$(PYTHON) scripts/validate_source.py apps.json \
		--repository ICANSII/icansii-sidestore \
		--check-releases

build: validate
	cp apps.json site/apps.json
	cp add-source.html site/add-source.html
	mkdir -p site/assets
	rsync -a assets/ site/assets/
	touch site/.nojekyll

clean:
	rm -rf site
