#!/bin/bash
# Reinstall gtars and refget on rivanna

ssh riva 'bash --login -s' << 'EOF'
set -e
source /etc/profile.d/modules.sh
module load miniforge/24.3.0-py3.11

# Build gtars (refget module only)
cd ~/code/gtars
git checkout dev
git pull
cd gtars-python
rm -f ../target/wheels/gtars-*.whl
maturin build --release --no-default-features --features refget
pip install ../target/wheels/gtars-*.whl --force-reinstall --no-deps

# Install local refget
cd ~/code/refget
git checkout dev
git pull
python -m pip install -e .

echo "Done!"
EOF
