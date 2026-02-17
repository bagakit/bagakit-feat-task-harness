SKILL_NAME := bagakit-feat-task-harness
BAGAKIT_HOME ?= $(HOME)/.bagakit
SKILL_DIR := $(BAGAKIT_HOME)/skills/$(SKILL_NAME)
PACKAGE := dist/$(SKILL_NAME).skill
AGENT_CLI ?= bagakit-agent
AGENT_FLAGS ?=

.PHONY: install-skill package-skill clean test agent-locale

install-skill:
	rm -rf "$(SKILL_DIR)"
	mkdir -p "$(SKILL_DIR)"
	cp -R SKILL.md README.md agents references scripts "$(SKILL_DIR)/"
	find "$(SKILL_DIR)/scripts" -type f -name "*.sh" -exec chmod +x {} +
	find "$(SKILL_DIR)/scripts" -type f -name "*.py" -exec chmod +x {} +
	@echo "installed: $(SKILL_DIR)"

package-skill: clean
	mkdir -p dist
	zip -r "$(PACKAGE)" SKILL.md README.md agents references scripts >/dev/null
	@echo "packaged: $(PACKAGE)"

test:
	./scripts_dev/test.sh

clean:
	rm -rf dist

agent-locale:
	@echo "BAGAKIT_HOME=$(PWD)/.bagakit"
	@echo "Running $(AGENT_CLI) with BAGAKIT_HOME=$(PWD)/.bagakit"
	$(AGENT_CLI) $(AGENT_FLAGS)
