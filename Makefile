.PHONY: install build test lint run all

install:
	pip install -e ".[dev]"

build:

lint:
	ruff check src tests scripts
	ruff format --check src tests scripts

test: build
	pytest

run: build
	python -m pillarchain run

all: lint test run

julia-test:
	julia --project=julia/PillarKernel -e 'using Pkg; Pkg.test()'
