# Raw Data Directory (Immutable)

This directory is designated for authentic, unaltered Level-1 SoLEXS light-curve FITS files and corresponding GTI FITS files downloaded directly from the official ISRO ISSDC PRADAN portal.

---

## Strict Immutability Rules
1. **Raw Files Are Immutable:**
   - Never edit, modify, resave, or overwrite any file in this directory.
   - Never rename a file after it has been indexed in `data/manifests/manifest.csv`.
   - Never run data cleaning, gap filling, or preprocessing scripts in-place inside `data/raw/`.
2. **Add Files Only With Manifest Entries:**
   - Add files to this directory only after recording their full metadata, observation IDs, and SHA-256 hashes in `data/manifests/manifest.csv`.
3. **Read-Only Access:**
   - All pipeline utilities and student analysis scripts must open files in this directory with read-only access (e.g., `fits.open(..., mode='readonly')`).
4. **No Automated or Mock Data:**
   - Do not programmatically create mock or synthetic FITS files in this directory.
