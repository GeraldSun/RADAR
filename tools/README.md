# RADAR Tools

This folder contains utility scripts for working with the RADAR DICOM image data.

## Contents

| File | Description |
|---|---|
| `view_dicom_metadata.py` | Scan a DICOM image directory and produce structured metadata summaries |
| `retrieve_series.py` | Use an LLM to select the most relevant CT series for each candidate edit |
| `metadata_dev_all_series.csv` | Precomputed series metadata for all dev-set cases |

---

## `view_dicom_metadata.py`

Recursively scans a root directory of CT cases organised as:

```
<root>/
  <case_id>/
    <series_folder>/   # e.g. ABD_PEL, LUNG_2.5mm
      *.dcm
```

For each series folder it groups DICOM files by `SeriesInstanceUID`, extracts key header fields (modality, slice thickness, pixel spacing, image size, instance number range), and writes:

- One plain-text summary per case to `metadata_<split>_txt/<case_id>.txt`
- A combined CSV to `metadata_<split>_all_series.csv`

**Configuration** — edit the path constants near the top of the script:

```python
ROOT_DIR        = Path("/path/to/images/<split>")
OUTPUT_DIR      = Path("/path/to/RADAR/tools")
TXT_OUTPUT_DIR  = OUTPUT_DIR / "metadata_<split>_txt"
CSV_OUTPUT_PATH = OUTPUT_DIR / "metadata_<split>_all_series.csv"
```

**Run:**

```bash
python tools/view_dicom_metadata.py
```

**Dependencies:** `pydicom`

---

## `retrieve_series.py`

Given the dev-set edits JSON and the precomputed series metadata CSV, uses a local LLM (via HuggingFace Transformers) to select the single most clinically relevant CT series for each candidate edit. The output is an enriched JSON file (`dev_edits_with_series.json`) where each edit gains two new fields:

- `selected_series` — the folder series name chosen by the model (e.g. `"ABD_PEL"`)
- `selected_series_reasoning` — a brief explanation (≤ 3 sentences)

**Configuration** — edit the path and model constants near the top of the script:

```python
EDITS_JSON   = "../data/dev_edits.json"
METADATA_CSV = "metadata_dev_all_series.csv"
OUTPUT_JSON  = "../data/dev_edits_with_series.json"
MODEL_PATH   = "/path/to/your/model"
```

**Run:**

```bash
python tools/retrieve_series.py
```

**Dependencies:** `torch`, `transformers`, `pandas`, `tqdm`

---

## `metadata_dev_all_series.csv`

Precomputed output of `view_dicom_metadata.py` for the dev split. Columns:

| Column | Description |
|---|---|
| `case_id` | Case identifier |
| `folder_series_name` | Human-readable series folder name (e.g. `ABD_PEL`) |
| `SeriesInstanceUID` | DICOM series UID |
| `SeriesNumber` | DICOM series number |
| `NumFiles` | Number of DICOM files in the series |
| `SeriesDescription` | DICOM series description string |
| `Modality` | DICOM modality (typically `CT`) |
| `SliceThickness` | Slice thickness in mm |
| `PixelSpacing` | In-plane pixel spacing |
| `ImageSize` | Rows × Columns (e.g. `512x512`) |
| `MinInstanceNumber` / `MaxInstanceNumber` | Instance number range |
| `InstanceNumberCompleteRange` | `YES` if the instance number range is contiguous |
| `Note` | Any anomalies detected (duplicate UIDs, missing files, etc.) |
