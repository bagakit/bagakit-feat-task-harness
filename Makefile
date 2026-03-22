SKILL_NAME := bagakit-feat-task-harness
BAGAKIT_HOME ?= $(HOME)/.bagakit
SKILL_DIR := $(BAGAKIT_HOME)/skills/$(SKILL_NAME)
PACKAGE := dist/$(SKILL_NAME).skill
AGENT_CLI ?= bagakit-agent
AGENT_FLAGS ?=

.PHONY: install-skill package-skill clean test test-preflight smoke-test agent-locale

install-skill:
	rm -rf "$(SKILL_DIR)"
	mkdir -p "$(SKILL_DIR)"
	cp -R SKILL.md SKILL_PAYLOAD.json README.md agents references scripts "$(SKILL_DIR)/"
	find "$(SKILL_DIR)/scripts" -type f -name "*.sh" -exec chmod +x {} +
	find "$(SKILL_DIR)/scripts" -type f -name "*.py" -exec chmod +x {} +
	@echo "installed: $(SKILL_DIR)"

package-skill: clean
	mkdir -p dist
	zip -r "$(PACKAGE)" SKILL.md SKILL_PAYLOAD.json README.md agents references scripts >/dev/null
	@echo "packaged: $(PACKAGE)"

test: test-preflight
	./scripts_dev/test.sh

test-preflight:
	@command -v python3 >/dev/null 2>&1 || { echo "missing: python3"; exit 1; }
	@command -v bash >/dev/null 2>&1 || { echo "missing: bash"; exit 1; }
	@command -v git >/dev/null 2>&1 || { echo "missing: git"; exit 1; }
	@command -v ruff >/dev/null 2>&1 || { echo "missing: ruff (install with 'brew install ruff' or 'python3 -m pip install --user ruff')"; exit 1; }
	@echo "ok: preflight"

smoke-test:
	python3 -m py_compile scripts/*.py
	bash -n scripts/*.sh scripts_dev/test.sh
	@echo "ok: smoke-test"

clean:
	rm -rf dist

agent-locale:
	@echo "BAGAKIT_HOME=$(PWD)/.bagakit"
	@echo "Running $(AGENT_CLI) with BAGAKIT_HOME=$(PWD)/.bagakit"
	$(AGENT_CLI) $(AGENT_FLAGS)
