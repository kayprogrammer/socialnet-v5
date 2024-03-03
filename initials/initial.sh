#! /usr/bin/env bash

# Run migrations
aerich upgrade

# Create initial data
python initials/initial_data.py

# Run tests
# pytest --verbose --disable-warnings -vv -x --timeout=10

# Start application
litestar run --debug --host 0.0.0.0 --port 8000 --reload 