PROJECT=meetingalarm

PIP ?= pip
PIP_CACHE ?=
PYTHON ?= python
ifeq (,$(PIP_CACHE))
PIP_OPTS =
else
PIP_OPTS = --cache-dir=$(PIP_CACHE)
endif

.PHONY: help
help:
	@echo "help           show this help"
	@echo "test           run all tests"
	@echo "setup-env      setup the virtual environment"
	@echo "install-dev    install the developer version of this project (modifiable)"
	@echo "resources      rebuild the resources"

.PHONY: test
test:
	nosetests

.PHONY: setup-env
setup-env:
	$(PIP) install $(PIP_OPTS) -r requirements.txt

.PHONY: resources
resources:
	@true

.PHONY: install
install:
	$(PIP) install $(PIP_OPTS) .

.PHONY: install-dev
install-dev:
	$(PIP) install $(PIP_OPTS) -e .

.PHONY: clean
clean:
	rm -rf build
	rm -rf *.egg-info
