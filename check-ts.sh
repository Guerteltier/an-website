#!/bin/sh
set -eu

pnpm install -q

FAILED=0

echo tsc:
pnpm tsc -p an_website || FAILED=$(( 2 | FAILED ))

echo ESLint:
pnpm eslint . || FAILED=$(( 4 | FAILED ))

exit "${FAILED}"
