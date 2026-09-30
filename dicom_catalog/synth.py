"""Generate small synthetic DICOM files (no real patient data) for demos and tests."""
from pathlib import Path

import numpy as np
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid


def write_series(out_dir: Path, patient_id: str, study_uid: str, modality: str,
                 series_number: int, n_images: int, study_date: str = "20260115",
                 skip: set[int] | None = None) -> str:
    series_uid = generate_uid()
    out_dir = Path(out_dir) / patient_id / study_uid[-8:] / f"S{series_number}"
    out_dir.mkdir(parents=True, exist_ok=True)
    for n in range(1, n_images + 1):
        if skip and n in skip:
            continue
        meta = FileMetaDataset()
        meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
        meta.MediaStorageSOPInstanceUID = generate_uid()
        meta.TransferSyntaxUID = ExplicitVRLittleEndian
        ds = FileDataset(None, {}, file_meta=meta, preamble=b"\0" * 128)
        ds.SOPClassUID = meta.MediaStorageSOPClassUID
        ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
        ds.PatientID, ds.PatientName, ds.PatientSex = patient_id, "SYNTHETIC^SUBJECT", "O"
        ds.PatientBirthDate = "19800101"
        ds.StudyInstanceUID, ds.StudyDate = study_uid, study_date
        ds.SeriesInstanceUID, ds.SeriesNumber, ds.InstanceNumber = series_uid, series_number, n
        ds.Modality, ds.SeriesDescription = modality, f"{modality} synthetic"
        ds.Rows = ds.Columns = 8
        ds.SamplesPerPixel, ds.PhotometricInterpretation = 1, "MONOCHROME2"
        ds.BitsAllocated, ds.BitsStored, ds.HighBit, ds.PixelRepresentation = 16, 12, 11, 0
        ds.PixelData = (np.arange(64, dtype=np.uint16) * n).tobytes()
        ds.save_as(out_dir / f"{n:04d}.dcm", enforce_file_format=True)
    return series_uid
