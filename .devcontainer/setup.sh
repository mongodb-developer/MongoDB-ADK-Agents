#!/bin/bash
#
# Python itself comes from the devcontainer python feature; this just installs
# the project's dependencies.

set -euo pipefail

echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt
