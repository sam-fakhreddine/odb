PYTHON ?= python3

.PHONY: groom-check gate-seam0
groom-check:
	$(PYTHON) scripts/groom_check.py $(if $(SEAM),--seam $(SEAM),)

gate-seam0:
	$(PYTHON) scripts/gate_seam0.py
