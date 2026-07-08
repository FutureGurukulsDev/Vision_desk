"""Durable local CSV export with optional SD-card mirror."""
import csv, os
from pathlib import Path
from threading import Lock
from flask import current_app
CSV_FIELDS=("id","name","company","phone","email","purpose","person_to_meet","status","arrival_time","photo_paths")
_lock=Lock()
def _append(path, record):
    path.parent.mkdir(parents=True,exist_ok=True); header=not path.exists() or path.stat().st_size==0
    with path.open("a",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=CSV_FIELDS,extrasaction="ignore")
        if header: writer.writeheader()
        writer.writerow({k:record.get(k,"") for k in CSV_FIELDS})
def append_visitor_to_csv(visitor):
    record=visitor.to_dict(); record["photo_paths"]=" | ".join(record.get("photo_paths",[]))
    paths=[Path(current_app.config["VISITOR_CSV_PATH"])]
    sd=os.environ.get("VISIONDESK_SD_CSV_PATH")
    if sd: paths.append(Path(sd))
    with _lock:
        for path in paths:
            try: _append(path,record)
            except OSError: current_app.logger.exception("Could not write visitor CSV to %s",path)