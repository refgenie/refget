# Schema Attribute Qualifiers

The refget seqcol implementation uses attribute qualifiers defined in the seqcol schema to control how attributes are stored, digested, and returned. This document explains how to add new attributes with different qualifiers.

## Attribute Qualifiers

According to the Refget Sequence Collections specification, attributes can have the following qualifiers:

- **inherent**: Attributes that contribute to the top-level digest (e.g., `names`, `sequences`)
- **collated**: Attributes whose values match 1-to-1 with sequences (e.g., `lengths`, `names`)
- **transient**: Attributes with no level 2 representation - only the digest is stored (e.g., `sorted_name_length_pairs`)
- **passthru**: Attributes that are NOT digested - they have the same value in level 1 and level 2 (currently none defined)

## How to Add a New Attribute

### Standard Attribute (Digested, Not Inherent)

Example: Adding a new `accessions` attribute that is digested but doesn't contribute to the top-level digest.

**1. Update the schema** (`schemas/seqcol.json`):
```json
{
  "properties": {
    "accessions": {
      "type": "array",
      "collated": true,
      "items": {"type": "string"}
    }
  },
  "ga4gh": {
    "inherent": ["names", "sequences"],
    "transient": ["sorted_name_length_pairs"],
    "passthru": []
  }
}
```

**2. Add to database model** (`refget/models.py`):
```python
class AccessionsAttr(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    value: list = Field(sa_column=Column(JSON), default_factory=list)
    collection: List["SequenceCollection"] = Relationship(back_populates="accessions")

class SequenceCollection(SQLModel, table=True):
    # ... existing fields ...
    accessions_digest: str = Field(foreign_key="accessionsattr.digest")
    accessions: "AccessionsAttr" = Relationship(back_populates="collection")
```

**3. Update `from_dict()` method** to compute digest and create attribute object
**4. Update `level1()` method** to return the digest: `"accessions": self.accessions.digest`
**5. Update `level2()` method** to return the value: `"accessions": self.accessions.value`

### Transient Attribute (Digest Only, No Value Storage)

Example: `sorted_name_length_pairs` is already transient.

**1. Update schema** to include in `ga4gh.transient` list

**2. Add to database model** (digest only, no Relationship):
```python
class SequenceCollection(SQLModel, table=True):
    # ... existing fields ...
    sorted_name_length_pairs_digest: str = Field()  # No foreign key, just digest
    # No Relationship object - transient means we don't store the value
```

**3. Update `from_dict()`** to compute and store only the digest
**4. Update `level1()`** to return the digest: `"sorted_name_length_pairs": self.sorted_name_length_pairs_digest`
**5. DO NOT include in `level2()`** - transient attributes have no level 2 representation

**Note**: Transient attributes must be manually kept in sync with the schema. Due to SQLModel/SQLAlchemy architectural constraints, models cannot be dynamically generated from schema at runtime (ORM requires class definitions at import time for database migrations).

### Passthru Attribute (Not Digested)

Example: Adding a `metadata` passthru attribute.

**1. Update schema**:
```json
{
  "properties": {
    "metadata": {
      "type": "object",
      "description": "Additional metadata about the collection"
    }
  },
  "ga4gh": {
    "inherent": ["names", "sequences"],
    "transient": ["sorted_name_length_pairs"],
    "passthru": ["metadata"]
  }
}
```

**2. Update constant** (`refget/const.py`):
```python
DEFAULT_PASSTHRU_ATTRS = ["metadata"]
```

**3. Add to database model** (value only, no digest):
```python
class MetadataAttr(SQLModel, table=True):
    # For passthru, we might want to use the value itself as primary key
    # or create a synthetic key - depends on use case
    id: str = Field(primary_key=True)
    value: dict = Field(sa_column=Column(JSON))
    collection: List["SequenceCollection"] = Relationship(back_populates="metadata")

class SequenceCollection(SQLModel, table=True):
    # ... existing fields ...
    metadata_id: str = Field(foreign_key="metadataattr.id")
    metadata: "MetadataAttr" = Relationship(back_populates="collection")
```

**4. Update `from_dict()`** to store the raw value (no digest computation)
**5. Update `level1()`** to return `.value` instead of `.digest`:
```python
def level1(self):
    return {
        # ... other attributes return .digest ...
        "metadata": self.metadata.value,  # Passthru: return value, not digest
    }
```
**6. Update `level2()`** to return the value: `"metadata": self.metadata.value` (same as level1!)

### Inherent Attribute (Contributes to Top-Level Digest)

**1. Update schema** to include in `ga4gh.inherent` list

**2. Update constant** (`refget/const.py`):
```python
DEFAULT_INHERENT_ATTRS = ["names", "sequences", "your_new_attr"]
```

**3. Follow steps for standard attribute** - the inherent qualifier only affects digest computation, not storage

The `seqcol_digest()` function automatically filters to only inherent attributes when computing the top-level digest, so no other code changes needed.

## Important Notes

- **Collated validation**: If you mark an attribute as `collated: true`, ensure all collated attributes have the same length (validation for this is still TODO - see issue #5 in compliance plan)
- **Database migrations**: After modifying models, run `alembic revision --autogenerate -m "Add new attribute"` to generate a database migration
- **Testing**: Add tests for new attributes in `tests/local/test_local_models.py`
