#!/bin/bash
# env/deploy-deps.sh — Build and install dependencies on Rivanna from mutagen-synced source
#
# Requires: DEPLOY_HOST and DEPLOY_DIR set in env file
# Requires: mutagen syncs running (via mutagen-setup.sh)

if [ -z "$DEPLOY_HOST" ] || [ -z "$DEPLOY_DIR" ]; then
  echo "DEPLOY_HOST and DEPLOY_DIR must be set. Source your env file first."
  exit 1
fi

ssh "$DEPLOY_HOST" 'bash --login -s' << EOF
set -e
source /etc/profile.d/modules.sh
module load miniforge/24.3.0-py3.11

# Build gtars from synced source
cd ${DEPLOY_DIR}/gtars/gtars-python
rm -f ../target/wheels/gtars-*.whl
echo "Building gtars..."
maturin build --release --no-default-features --features refget
pip install ../target/wheels/gtars-*.whl --force-reinstall --no-deps
echo "gtars installed."

# Install refget from synced source
cd ${DEPLOY_DIR}/refget
echo "Installing refget..."
python -m pip install -e .
echo "refget installed."

echo "Done!"
EOF
