#!/bin/sh
set -eu

npm --prefix frontend ci --include=dev
npm --prefix frontend run build
python scripts/check_frontend.py
