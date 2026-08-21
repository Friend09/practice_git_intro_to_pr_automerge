.PHONY: install compile run-notebooks clean test help pr

PYTHON := python
UV := uv

# ── Installation ───────────────────────────────────────────────────────────────
install: requirements.txt
	$(UV) pip install -r requirements.txt

requirements.txt: requirements.in
	$(UV) pip compile requirements.in -o requirements.txt

compile: requirements.txt

# ── Labs ───────────────────────────────────────────────────────────────────────
lab-%:
	$(PYTHON) labs/lab_$(*)_*.py

# ── Notebooks ─────────────────────────────────────────────────────────────────
run-notebooks:
	@echo "Running all notebooks and saving cleared outputs..."
	jupyter nbconvert --to notebook --execute --inplace notebooks/practice_*.ipynb
	@echo "Stripping outputs for clean commits..."
	jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace notebooks/practice_*.ipynb

# ── Sandbox PRs ───────────────────────────────────────────────────────────────
# Generate a throwaway PR of a known size against sandbox/, e.g.:
#   make pr LINES=120 FILES=6
pr:
	$(PYTHON) sandbox/generate_pr.py --lines $(LINES) --files $(FILES)

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	pytest tests/ -v --tb=short

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} + 2>/dev/null || true
	rm -rf output/*.html output/*.json 2>/dev/null || true

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo "Available targets:"
	@echo "  install          Install dependencies"
	@echo "  compile          Compile requirements.in -> requirements.txt"
	@echo "  run-notebooks    Execute + strip all notebook outputs (clean commits)"
	@echo "  pr LINES=N FILES=M   Generate a throwaway sandbox PR of a known size"
	@echo "  test             Run test suite"
	@echo "  clean            Remove __pycache__, .pyc, .ipynb_checkpoints"
	@echo "  lab-XX           Run a lab script, e.g. make lab-01"
