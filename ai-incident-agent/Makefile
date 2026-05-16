VENV ?= .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

all: install

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel

test: install
	$(PYTHON) -m pytest tests/test_agent.py

run: install
	$(PYTHON) -m ai_incident_agent.runner

monitor: install
	$(PYTHON) -m ai_incident_agent.runner

web: install
	$(PYTHON) -m ai_incident_agent.web_runner

install: $(VENV)/bin/activate
	$(PIP) install -e .
	$(PIP) install -r requirements.txt

clean:
	rm -rf $(VENV) build dist *.egg-info .pytest_cache
