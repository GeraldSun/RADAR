# RADAR Baselines

This folder contains baseline notebooks for the RADAR benchmark. Four notebooks are provided, covering two multimodal models and two strategies for feeding 3D CT volumes to 2D/video-capable models.

## Notebooks

| Notebook | Model | CT Input Strategy |
|---|---|---|
| `gemini_video.ipynb` | Google Gemini | DICOM slices assembled into an MP4 video |
| `gemini_slice.ipynb` | Google Gemini | DICOM slices sent as individual images |
| `qwen_video.ipynb` | Qwen-VL | DICOM slices assembled into an MP4 video |
| `qwen_slice.ipynb` | Qwen-VL | DICOM slices sent as individual images |

---

## Input Strategy Details

### Slice mode
Selected DICOM slices from the relevant CT series are windowed (soft-tissue or lung window), converted to PNG, and sent to the model as a list of images alongside the preliminary report text and the candidate edit.

### Video mode
Selected slices are assembled into a short MP4 video at a fixed frame rate (`VIDEO_FPS`, default 10 fps), capped at `MAX_SLICE` frames. The video is uploaded to the model API (or passed inline) and the model reasons over the full volumetric sweep together with the text context.

---

## Setup

### Gemini notebooks

Install the Google GenAI SDK:

```bash
pip install google-genai
```

Set your API key in the notebook or as an environment variable:

```python
os.environ["GEMINI_API_KEY"] = "<YOUR_GEMINI_API_KEY>"
```

### Qwen notebooks

The Qwen notebooks use a locally hosted Qwen-VL model via HuggingFace Transformers. Ensure the model weights are available and update the `MODEL_PATH` variable accordingly.

```bash
pip install transformers torch accelerate
```

---

## Common Dependencies

```
pydicom
numpy
pandas
pillow
imageio
tqdm
ipython
```

---

## Data Paths

Each notebook expects the following directory layout (matching the full RADAR dataset structure):

```
data/
  images/
    dev/
      <case_id>/
        <series_folder>/
          *.dcm
  dev_preliminary_report/
    <case_id>.txt
  dev_edits.json           # may be the enriched version with selected_series field
```

Update the path constants at the top of each notebook to point to your local data location.

---

## Output

Each notebook writes a CSV file with one row per edit:

```
edit_id, agreement_pred, severity_pred, edit_type_pred
```

This file can be passed directly to `eval/eval.py` for scoring.
