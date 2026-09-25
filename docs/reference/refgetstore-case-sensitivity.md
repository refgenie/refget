# Known RefgetStore Limitation: Case-Insensitive File System Conflicts

## Summary

RefgetStore fails to properly store and retrieve sequences when running on case-insensitive file systems (like Dropbox-synced directories) due to sha512t24u digest prefixes differing only in case.

## Symptoms

- `export_fasta()` fails with: "File not found locally and no remote source configured"
- Some sequences are recorded in the index but missing from disk
- Example: 610 sequences in index, but only 588 sequence files exist

## Root Cause

RefgetStore uses the first 2 characters of sha512t24u digests as directory prefixes (e.g., `sequences/Lc/`). Base64url encoding produces case-sensitive characters, so directories like `0F` and `0f` can exist.

On case-insensitive file systems (macOS default, Dropbox sync on Linux), these create conflicts:
- `0F` directory is created first
- `0f` directory cannot be created (or gets renamed to "0f (Case Conflict)")
- Sequences with `0f` prefix never get written

## Evidence

```
$ ls sequences/ | grep -i "^0f"
0F
0f (Case Conflict)
```

Missing prefixes (19 total): `0f, 4w, 9n, Iq, Lc, Lq, Pj, Pq, Rc, Rr, Te, Tq, Uu, aw, dg, fu, iz, ji, vr`

All correspond to Dropbox case conflicts, not gtars logic errors.

## Workarounds

1. Store RefgetStore databases on local disk (not Dropbox/iCloud synced directories)
2. Use a case-sensitive file system
3. Use longer prefixes (3+ chars) to reduce collision probability

## Potential Fixes

1. **Normalize to lowercase**: Use `prefix.lower()` for all directory names --
2. **Use hex encoding**: Replace base64url with hex for prefixes (only 0-9, a-f)
3. **Detect and handle conflicts**: Check for case conflicts before writing

## Environment

- gtars version: 0.5.2
- File system: Dropbox-synced directory on Linux (ext4, but Dropbox enforces case-insensitivity)
- Input: HG002 pangenome FASTA (610 sequences)

## Additional insights:

- it's not just the folder structure, but the sequence file names that are also case sensitive.
- even if you solved this problem for folders (eg using `lower()`), it could lead to clashes in the .seq file paths.
- so it could be dangerous to use on a case-insensitive filesystem just because it increases probability of clashes.
- nevertheless, it might still work for smaller databases where clash risk is lower?