.PHONY: test test-l1 test-l2 eval-component eval-handoff bench-l3 lint

EVAL_PROFILE ?= smoke

test:
	python3 -m pytest tests/ -q

test-l1:
	@echo "test-l1 is deprecated; running deterministic tests"
	python3 -m pytest tests/ -q

test-l2:
	@echo "test-l2 is deprecated; use eval-handoff"
	python3 -m pytest evals/handoff/ --collect-only -q

eval-component:
	python3 -m pytest evals/component/ -v --eval-profile $(EVAL_PROFILE)

eval-handoff:
	python3 -m pytest evals/handoff/ -v --eval-profile $(EVAL_PROFILE)

bench-l3:
	python3 -m benchmarks.runner.cli run --entry bench-001 --runs 5

lint:
	find benchmarks/entries evals \( -name "*.yaml" -o -name "*.yml" \) | while read f; do python3 -c "import yaml; yaml.safe_load(open('$$f'))" || exit 1; done
	find docs -name "*.md" -not -name "README.md" | while read f; do head -1 "$$f" | grep -q "^---$$" || echo "WARN: $$f missing frontmatter"; done
