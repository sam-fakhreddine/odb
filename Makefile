PYTHON ?= python3

.PHONY: groom-check gate-seam0 gate-seam8 type-check schema-check
groom-check:
	$(PYTHON) scripts/groom_check.py $(if $(SEAM),--seam $(SEAM),)

gate-seam0:
	$(PYTHON) scripts/gate_seam0.py

gate-seam8:
	$(PYTHON) scripts/gate_seam0.py --seam 8

type-check:
	$(PYTHON) scripts/check_types.py

schema-check:
	$(PYTHON) -m aws_emulator_shim.schema --check docs/schemas/manifest-v1.schema.json
