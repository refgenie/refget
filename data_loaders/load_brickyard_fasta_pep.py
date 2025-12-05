import os
import json

import pephubclient
from refget import add_fasta_pep
from refget.agents import RefgetDBAgent

phc = pephubclient.PEPHubClient()
p = phc.load_project("donaldcampbelljr/human_mouse_fasta_brickyard:default")
fa_root = ""  # PEP has absolute paths in the fasta column

# Cloud storage configuration from environment (JSON array)
# Example: '[{"bucket": "my-bucket", "prefix": "fasta/", "cloud": "aws", "region": "us-east-1"},
#           {"bucket": "my-azure-container", "prefix": "", "cloud": "azure", "region": "eastus"}]'
storage = json.loads(os.environ.get("FASTA_STORAGE_LOCATIONS", "[]")) or None

# Initialize database agent
dbc = RefgetDBAgent()
print(f"SQL Engine: {dbc.engine}")

# Add FASTAs to database (and optionally upload to cloud storage)
print("Adding FASTAs to database...")
results = add_fasta_pep(p, fa_root, dbagent=dbc, storage=storage)

with open("frontend/src/assets/brickyard_fasta.json", "w") as f:
    f.write(json.dumps(results, indent=2))

print("\nDone. Results saved to frontend/src/assets/brickyard_fasta.json")
