# PEPhub Client: Issues Encountered

## 1. `--force` doesn't update samples on existing projects

**Problem:** `phc push --force` and `phc.upload(force=True)` return success (202) but silently fail to update the sample table when the project already exists. The config/metadata may update, but samples remain unchanged.

**Workaround:** Delete the project first, then push fresh:

```python
import requests
from pephubclient import PEPHubClient

phc = PEPHubClient()
jwt = phc._PEPHubClient__jwt_data
headers = {"Authorization": f"Bearer {jwt}"}

requests.delete(
    "https://pephub-api.databio.org/api/v1/projects/NAMESPACE/PROJECT",
    params={"tag": "TAG"},
    headers=headers,
)
```

Then push normally with `phc push`.

## 2. Bare CSV push fails with 400

**Problem:** The CLI help says `CFG` accepts "Project config file (YAML) or sample table (CSV/TSV)", but pushing a bare CSV fails with `Unexpected Response Error. 400`.

**Workaround:** Always push a YAML config that references the CSV:

```yaml
# project_config.yaml
pep_version: "2.1.0"
sample_table: samples.csv
name: my_project
```

```bash
phc push --namespace NS --name NAME --tag TAG project_config.yaml
```

## 3. `phc.upload()` with peppy Project reports success but uploads empty samples

**Problem:** Loading a project with `phc.load_project()`, modifying `sample_table` in-place, then calling `phc.upload()` reports success but the server receives no samples. The `project.to_dict()` output is correct (verified locally), so the issue is server-side.

**Workaround:** Write the modified sample table to a CSV, create a YAML config referencing it, and use `phc push` with the YAML.
