PYTHON ?= python3
RUFF ?= ruff
GUIDE := coding-guide/scripts
PREFIX ?= /usr/local
APP_DIR := $(PREFIX)/share/depman
DESKTOP_FILE := io.github.depman.DepMan.desktop

.PHONY: run check check-fast format ratchet-update screenshot deb install uninstall

run:
	$(PYTHON) -m depman

check:
	$(RUFF) format --check .
	$(RUFF) check .
	$(PYTHON) $(GUIDE)/layering.py
	$(PYTHON) $(GUIDE)/ratchet.py check
	xvfb-run -a $(PYTHON) -m pytest -q

check-fast:
	$(RUFF) check .
	$(PYTHON) $(GUIDE)/layering.py
	$(PYTHON) -m pytest -q -m "not ui"

format:
	$(RUFF) format .
	$(RUFF) check --fix .

ratchet-update:
	$(PYTHON) $(GUIDE)/ratchet.py update

screenshot:
	xvfb-run -a -s "-screen 0 1280x800x24" $(PYTHON) -m tests.screenshots

deb:
	sh packaging/build-deb.sh

# Distro-independent install: plain files, no pip. Packagers pass DESTDIR and PREFIX=/usr.
install:
	install -d $(DESTDIR)$(APP_DIR) $(DESTDIR)$(PREFIX)/bin $(DESTDIR)$(PREFIX)/share/applications
	cp -r depman $(DESTDIR)$(APP_DIR)/
	find $(DESTDIR)$(APP_DIR) -name __pycache__ -prune -exec rm -rf {} +
	sed 's|@APP_DIR@|$(APP_DIR)|' data/depman.in > $(DESTDIR)$(PREFIX)/bin/depman
	chmod 755 $(DESTDIR)$(PREFIX)/bin/depman
	install -m 644 data/$(DESKTOP_FILE) $(DESTDIR)$(PREFIX)/share/applications/$(DESKTOP_FILE)

uninstall:
	rm -rf $(DESTDIR)$(APP_DIR)
	rm -f $(DESTDIR)$(PREFIX)/bin/depman $(DESTDIR)$(PREFIX)/share/applications/$(DESKTOP_FILE)
