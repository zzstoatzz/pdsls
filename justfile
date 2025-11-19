# generate api reference docs with mdxify
generate-docs:
    uv run mdxify --all --root-module pdsx --output-dir docs/api-reference --include-internal

# run tests
test:
    uv run pytest tests/ -xvs

# format and lint
fmt:
    uv run ruff format src/ tests/
    uv run ruff check src/ tests/ --fix

# type check
check:
    uv run ty check

serve-docs:
    cd docs && bunx mint@latest dev