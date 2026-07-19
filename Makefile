.PHONY: test-l1 test-l2 bench-l3 lint

test-l1:
	python3 -m pytest tests/unit/ -v

test-l2:
	python3 -m pytest tests/integration/ -v

bench-l3:
	python3 -m benchmarks.runner.cli run --entry bench-001 --runs 5

lint:
	python3 -c "import yaml; [yaml.safe_load(open(f'benchmarks/entries/{e}/expected.yaml')) for e in ['bench-001']]" 2>/dev/null || true
	find docs -name "*.md" -not -name "README.md" | while read f; do head -1 "$$f" | grep -q "^---$$" || echo "WARN: $$f missing frontmatter"; done