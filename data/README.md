# RADAR Data

This folder contains **example** data for the RADAR shared task.

## Contents

- `example_preliminary_report/` — Two anonymized example preliminary radiology reports (cases 11001 and 11002) illustrating the text format used in the full dataset.
- `example_edits.json` — Example candidate edits for each of the two example reports, following the same JSON schema as the full release.

## Data Format

### Preliminary Reports (`example_preliminary_report/*.txt`)
Each `.txt` file corresponds to one case and contains a de-identified preliminary inpatient radiology report authored overnight or during daytime hours before attending review.

### Edits (`example_edits.json`)
A JSON array where each element contains:
- `case_id` — integer identifier matching the report filename
- `clinical_indication` — de-identified clinical question posed to the radiologist
- `preliminary_report_time` — `"overnight"` or `"daytime"`
- `edits` — list of candidate edit objects, each with:
  - `edit_id` — unique string identifier (e.g., `"10001_01"`)
  - `suggested_edit_text` — the proposed addition, correction, or clarification to the preliminary report

## Images

Each case is accompanied by one or more CT image series in DICOM format. Because the DICOM files are large and subject to the same Data Use Agreement as the text data, they are not included in this repository.

When the full dataset is released, the image files should be placed under an `images/` subdirectory alongside the text data, following this layout:

```
data/
  images/
    dev/
      <case_id>/
        <series_folder>/    # e.g. ABD_PEL, LUNG_2.5mm
          *.dcm
  dev_preliminary_report/
    <case_id>.txt
  dev_edits.json
```

The `<case_id>` directory names match the integer identifiers used in the edits JSON and the report filenames. Each `<series_folder>` contains the DICOM slices for one CT acquisition series. Utility scripts for browsing series metadata and selecting the most relevant series per edit are provided in the `tools/` folder.

---

## Requesting the Full Dataset

The example files in this folder are provided for reference only. The full RADAR dataset contains 50 de-identified cases and is subject to a **Data Use Agreement (DUA)**.

To request access to the full dataset, please contact the authors listed in the [paper](https://arxiv.org/abs/2603.06681).

Your request should include your name, institutional affiliation, and a brief description of your intended use. A signed DUA is required before data will be released.

Participants in the [ImageCLEFmed MEDIQA-CORE 2026 shared task](https://ai4media-bench.aimultimedialab.ro/competitions/7/) may access the dataset through the official competition platform.
