# Windows-friendly Makefile (requires GNU make)

.PHONY: analyze run _run test %

ARGS := $(filter-out $@,$(MAKECMDGOALS))

analyze:
	uv run vcer analyze --in examples/system.md --user examples/user.md --out parts.json

run:
	@if [ -z "$(word 1,$(ARGS))" ]; then \
		echo "Usage: make run http://host:port/endpoint"; \
		exit 1; \
	fi; \
	$(MAKE) _run ENDPOINT=$(word 1,$(ARGS))

_run:
	@echo Routing to $(ENDPOINT)
	uv run vcer route \
		--backend openai \
		--endpoint "$(ENDPOINT)" \
		--model gpt-oss:20b \
		--header "Authorization: Bearer ollama" \
		--system examples/system.md \
		--user examples/user.md \
		--send

test:
	$(MAKE) run http://localhost:11434/v1/chat/completions

%:
	@:

