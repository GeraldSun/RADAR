import csv
from pathlib import Path
from collections import defaultdict
import pydicom


ROOT_DIR = Path("/home/NETID/zhaoyis/code/RADAR_for_organizers/data/images/test")
OUTPUT_DIR = Path("/home/NETID/zhaoyis/code/RADAR/tools")
TXT_OUTPUT_DIR = OUTPUT_DIR / "metadata_test_txt"
CSV_OUTPUT_PATH = OUTPUT_DIR / "metadata_test_all_series.csv"

TXT_OUTPUT_DIR.mkdir(exist_ok=True)


def is_probably_dicom(file_path: Path) -> bool:
    """
    Return True if the file can be read as a DICOM file.
    """
    if not file_path.is_file():
        return False

    try:
        with open(file_path, "rb") as f:
            header = f.read(132)
        if len(header) >= 132 and header[128:132] == b"DICM":
            return True
    except Exception:
        pass

    try:
        pydicom.dcmread(str(file_path), stop_before_pixels=True, force=True)
        return True
    except Exception:
        return False


def safe_get(ds, attr, default=""):
    """
    Safely get a DICOM attribute.
    """
    return getattr(ds, attr, default)


def safe_str(value):
    """
    Convert pydicom values to a clean string.
    """
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:
        return ""


def read_dicom_header(file_path: Path):
    """
    Read a DICOM header without pixel data.
    """
    return pydicom.dcmread(str(file_path), stop_before_pixels=True, force=True)


def collect_dicom_files(series_folder: Path):
    """
    Collect all readable DICOM files in a folder.
    """
    dicom_files = []
    for f in sorted(series_folder.iterdir()):
        if is_probably_dicom(f):
            dicom_files.append(f)
    return dicom_files


def group_files_by_series_uid(dicom_files):
    """
    Group files by SeriesInstanceUID.
    Files missing SeriesInstanceUID are grouped under '__MISSING_SERIES_UID__'.
    """
    groups = defaultdict(list)

    for f in dicom_files:
        try:
            ds = read_dicom_header(f)
            series_uid = safe_str(safe_get(ds, "SeriesInstanceUID", "__MISSING_SERIES_UID__"))
            if not series_uid:
                series_uid = "__MISSING_SERIES_UID__"
            groups[series_uid].append((f, ds))
        except Exception:
            groups["__FAILED_READ__"].append((f, None))

    return groups


def sort_group_items(items):
    """
    Sort files in one SeriesInstanceUID group using:
    1. InstanceNumber
    2. ImagePositionPatient z
    3. filename
    """
    sortable = []

    for f, ds in items:
        instance_number = None
        z_pos = None

        if ds is not None:
            try:
                instance_number = safe_get(ds, "InstanceNumber", None)
                if instance_number is not None:
                    instance_number = int(instance_number)
            except Exception:
                instance_number = None

            try:
                ipp = safe_get(ds, "ImagePositionPatient", None)
                if ipp is not None and len(ipp) >= 3:
                    z_pos = float(ipp[2])
            except Exception:
                z_pos = None

        sortable.append((f, ds, instance_number, z_pos))

    sortable.sort(
        key=lambda x: (
            x[2] is None,                       # prefer files with InstanceNumber
            x[2] if x[2] is not None else 0,
            x[3] is None,                       # then prefer files with z position
            x[3] if x[3] is not None else 0.0,
            x[0].name
        )
    )
    return sortable


def summarize_one_true_series(case_id, folder_name, series_uid, items):
    """
    Summarize one true DICOM series (one SeriesInstanceUID group).
    """
    sorted_items = sort_group_items(items)
    first_file, first_ds, _, _ = sorted_items[0]

    info = {
        "case_id": case_id,
        "folder_series_name": folder_name,
        "SeriesInstanceUID": series_uid,
        "SeriesNumber": "NA",
        "NumFiles": len(items),
        "NumUniqueSOPInstanceUIDs": "",
        "SeriesDescription": "",
        "Modality": "",
        "SliceThickness": "",
        "PixelSpacing": "",
        "ImageSize": "",
        "FirstFileName": first_file.name,
        "MinInstanceNumber": "",
        "MaxInstanceNumber": "",
        "InstanceNumberCompleteRange": "",
        "Note": ""
    }

    if first_ds is None:
        info["Note"] = "Failed to read representative header"
        return info

    info["SeriesNumber"] = safe_str(safe_get(first_ds, "SeriesNumber", "NA"))
    info["SeriesDescription"] = safe_str(safe_get(first_ds, "SeriesDescription", ""))
    info["Modality"] = safe_str(safe_get(first_ds, "Modality", ""))
    info["SliceThickness"] = safe_str(safe_get(first_ds, "SliceThickness", ""))
    info["PixelSpacing"] = safe_str(safe_get(first_ds, "PixelSpacing", ""))

    rows = safe_get(first_ds, "Rows", "")
    cols = safe_get(first_ds, "Columns", "")
    if rows != "" and cols != "":
        info["ImageSize"] = f"{rows}x{cols}"

    sop_uids = set()
    instance_numbers = []

    for _, ds, inst_num, _ in sorted_items:
        if ds is not None:
            sop_uid = safe_str(safe_get(ds, "SOPInstanceUID", ""))
            if sop_uid:
                sop_uids.add(sop_uid)
        if inst_num is not None:
            instance_numbers.append(inst_num)

    info["NumUniqueSOPInstanceUIDs"] = len(sop_uids)

    if instance_numbers:
        min_inst = min(instance_numbers)
        max_inst = max(instance_numbers)
        info["MinInstanceNumber"] = min_inst
        info["MaxInstanceNumber"] = max_inst

        expected_n = max_inst - min_inst + 1
        info["InstanceNumberCompleteRange"] = "YES" if expected_n == len(set(instance_numbers)) else "NO"

    if len(sop_uids) != len(items):
        info["Note"] = (info["Note"] + "; " if info["Note"] else "") + \
                       "Duplicate or missing SOPInstanceUID detected"

    return info


def process_one_folder(case_id, folder_path: Path):
    """
    Process one human-readable series folder, such as ABD_PEL.
    May contain one or more true DICOM series.
    """
    folder_name = folder_path.name
    dicom_files = collect_dicom_files(folder_path)

    if not dicom_files:
        return [{
            "case_id": case_id,
            "folder_series_name": folder_name,
            "SeriesInstanceUID": "",
            "SeriesNumber": "NA",
            "NumFiles": 0,
            "NumUniqueSOPInstanceUIDs": "",
            "SeriesDescription": "",
            "Modality": "",
            "SliceThickness": "",
            "PixelSpacing": "",
            "ImageSize": "",
            "FirstFileName": "",
            "MinInstanceNumber": "",
            "MaxInstanceNumber": "",
            "InstanceNumberCompleteRange": "",
            "Note": "No readable DICOM files found"
        }]

    uid_groups = group_files_by_series_uid(dicom_files)
    rows = []

    for series_uid, items in uid_groups.items():
        info = summarize_one_true_series(case_id, folder_name, series_uid, items)
        rows.append(info)

    if len(uid_groups) > 1:
        for row in rows:
            row["Note"] = (row["Note"] + "; " if row["Note"] else "") + \
                          f"Folder contains multiple SeriesInstanceUID groups ({len(uid_groups)})"

    return sorted(rows, key=lambda x: (x["folder_series_name"], x["SeriesNumber"], x["SeriesInstanceUID"]))


def write_case_txt(case_id, rows, out_dir: Path):
    """
    Write one text summary per case.
    """
    out_path = out_dir / f"{case_id}.txt"
    lines = [f"case_id: {case_id}", "=" * 90]

    if not rows:
        lines.append("No series folders found.")
    else:
        for row in rows:
            lines.append(f"FolderSeriesName: {row['folder_series_name']}")
            lines.append(f"SeriesInstanceUID: {row['SeriesInstanceUID']}")
            lines.append(f"SeriesNumber: {row['SeriesNumber']}")
            lines.append(f"NumFiles: {row['NumFiles']}")
            lines.append(f"NumUniqueSOPInstanceUIDs: {row['NumUniqueSOPInstanceUIDs']}")
            if row["SeriesDescription"]:
                lines.append(f"SeriesDescription: {row['SeriesDescription']}")
            if row["Modality"]:
                lines.append(f"Modality: {row['Modality']}")
            if row["SliceThickness"]:
                lines.append(f"SliceThickness: {row['SliceThickness']}")
            if row["PixelSpacing"]:
                lines.append(f"PixelSpacing: {row['PixelSpacing']}")
            if row["ImageSize"]:
                lines.append(f"ImageSize: {row['ImageSize']}")
            if row["FirstFileName"]:
                lines.append(f"FirstFileName: {row['FirstFileName']}")
            if row["MinInstanceNumber"] != "":
                lines.append(f"MinInstanceNumber: {row['MinInstanceNumber']}")
            if row["MaxInstanceNumber"] != "":
                lines.append(f"MaxInstanceNumber: {row['MaxInstanceNumber']}")
            if row["InstanceNumberCompleteRange"] != "":
                lines.append(f"InstanceNumberCompleteRange: {row['InstanceNumberCompleteRange']}")
            if row["Note"]:
                lines.append(f"Note: {row['Note']}")
            lines.append("-" * 90)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved txt: {out_path}")


def write_csv(rows, out_path: Path):
    """
    Write combined CSV.
    """
    fieldnames = [
        "case_id",
        "folder_series_name",
        "SeriesInstanceUID",
        "SeriesNumber",
        "NumFiles",
        "NumUniqueSOPInstanceUIDs",
        "SeriesDescription",
        "Modality",
        "SliceThickness",
        "PixelSpacing",
        "ImageSize",
        "FirstFileName",
        "MinInstanceNumber",
        "MaxInstanceNumber",
        "InstanceNumberCompleteRange",
        "Note"
    ]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved csv: {out_path}")


def main():
    all_rows = []

    case_dirs = [d for d in sorted(ROOT_DIR.iterdir()) if d.is_dir()]
    case_dirs = [d for d in case_dirs if not d.name.startswith("_")]

    if not case_dirs:
        print(f"No case folders found in {ROOT_DIR}")
        return

    for case_dir in case_dirs:
        case_id = case_dir.name
        folder_paths = [d for d in sorted(case_dir.iterdir()) if d.is_dir()]

        case_rows = []
        for folder_path in folder_paths:
            rows = process_one_folder(case_id, folder_path)
            case_rows.extend(rows)
            all_rows.extend(rows)

        write_case_txt(case_id, case_rows, TXT_OUTPUT_DIR)

    write_csv(all_rows, CSV_OUTPUT_PATH)


if __name__ == "__main__":
    main()