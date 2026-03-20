import os
os.environ["CUDA_VISIBLE_DEVICES"] = "3"

import json
import re
import pandas as pd
import torch
from tqdm.auto import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM

# ---- Paths ----
EDITS_JSON   = os.path.join(os.path.dirname(__file__), "../data/dev_edits.json")
METADATA_CSV = os.path.join(os.path.dirname(__file__), "metadata_dev_all_series.csv")
OUTPUT_JSON  = os.path.join(os.path.dirname(__file__), "../data/dev_edits_with_series.json")
MODEL_PATH   = "/home/bionlp/pubmodels/openai/gpt-oss-20b/"

# ---- System prompt ----
PROMPT_SYSTEM = """
You are an assistant that links CT report suggested edits to the CT image series that a radiologist would most likely refer to.

Use the following inputs:
  - Clinical indication
  - Series list (SeriesNumber and description)
  - One candidate suggested edit

For each edit, choose the CT series that a radiologist would actually review when formulating that specific edit.

You MUST exactly output the most relevant folder series name (e.g. "ABD_PEL", "LUNG_2.5mm").

Matching logic:
  - Prefer series whose description best matches the anatomic region and purpose of the edit (e.g., lung, mediastinum, abdomen, bone, angiographic phase, etc.).
  - Use the clinical indication and any mentioned organ to disambiguate when multiple series are plausible.

Output format:
  - Your response MUST be valid JSON with DOUBLE QUOTES and NO trailing commas.
  - JSON schema:

   {
     "selected_folder_series_name": string,  // e.g. "ABD_PEL", "LUNG_2.5mm"
     "reasoning": string                     // max 3 sentences
   }
""".strip()


def build_series_info(rows: list[dict]) -> str:
    """Build a formatted series list string from a list of metadata dicts for one case."""
    lines = ["Found series:"]
    for row in rows:
        lines.append(
            f"  FolderName={row['folder_series_name']}"
            f"   | Modality={row['Modality']}"
            f" | n={row['NumFiles']}"
            f" | {row['SeriesDescription']}"
        )
    return "\n".join(lines)


def main():
    # ---- Load inputs ----
    with open(EDITS_JSON) as f:
        cases = json.load(f)

    df_meta = pd.read_csv(METADATA_CSV)
    df_meta["case_id"] = df_meta["case_id"].astype(str)

    # Build series_info string per case_id and attach to each case
    series_info_map: dict[str, str] = {}
    for case_id, group in df_meta.groupby("case_id"):
        rows = group[["Modality", "NumFiles", "SeriesDescription",
                       "folder_series_name"]].to_dict("records")
        series_info_map[str(case_id)] = build_series_info(rows)

    for case in cases:
        case["series_info"] = series_info_map.get(str(case["case_id"]), "No series found.")

    # ---- Load model ----
    print(f"Loading model from {MODEL_PATH} ...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, device_map="cuda")
    print("Model loaded.")

    # ---- Inference loop: iterate over cases then edits ----
    total_edits = sum(len(case.get("edits", [])) for case in cases)
    pbar = tqdm(total=total_edits, desc="Processing edits")

    for case in cases:
        case_id             = str(case["case_id"])
        clinical_indication = case.get("clinical_indication", "")
        series_info         = case.get("series_info", "")

        for edit in case.get("edits", []):
            user_content = (
                f"Case ID: {case_id}\n"
                f"Clinical indication: {clinical_indication}\n\n"
                f"Series list:\n{series_info}\n\n"
                f"Suggested edit: {edit['suggested_edit_text']}\n"
            )

            messages = [
                {"role": "system", "content": PROMPT_SYSTEM},
                {"role": "user",   "content": user_content},
            ]

            inputs = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            ).to("cuda")

            with torch.inference_mode():
                outputs = model.generate(**inputs, max_new_tokens=32768)

            decoded = tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[-1]:],
                skip_special_tokens=False,
            )

            edit["series_output"] = decoded

            final_match = re.search(
                r"<\|channel\|>final<\|message\|>(.*?)<\|return\|>",
                decoded,
                re.DOTALL,
            )
            final_text = final_match.group(1).strip() if final_match else None

            if final_text is not None:
                obj = json.loads(final_text)
                edit["selected_series"]           = obj.get("selected_folder_series_name")
                edit["selected_series_reasoning"] = obj.get("reasoning")
            else:
                edit["selected_series"]           = None
                edit["selected_series_reasoning"] = None

            pbar.update(1)

    pbar.close()

    # ---- Save enriched JSON ----
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(cases, f, indent=2)
    print(f"Results saved to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
