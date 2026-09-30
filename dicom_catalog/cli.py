import argparse
from pathlib import Path

from pydicom.uid import generate_uid

from . import __version__
from .db import connect, init_schema
from .ingest import ingest_directory
from .report import run_report
from .synth import write_series


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="dicom-catalog")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="create tables")
    ing = sub.add_parser("ingest", help="catalog a directory of DICOM files")
    ing.add_argument("source", type=Path)
    ing.add_argument("--project", required=True)
    sub.add_parser("report", help="run data-quality checks")
    syn = sub.add_parser("synth", help="write synthetic demo data")
    syn.add_argument("out", type=Path)
    args = p.parse_args(argv)

    if args.cmd == "synth":
        for i, (mod, n) in enumerate([("MR", 12), ("CT", 20), ("PT", 6)], start=1):
            study = generate_uid()
            write_series(args.out, f"SUBJ{i:03d}", study, mod, 1, n)
            write_series(args.out, f"SUBJ{i:03d}", study, mod, 2, n // 2)
        print(f"wrote synthetic data to {args.out}")
        return

    with connect() as conn:
        init_schema(conn)
        if args.cmd == "ingest":
            print(ingest_directory(conn, args.source, args.project))
        elif args.cmd == "report":
            for name, rows in run_report(conn).items():
                print(f"\n== {name} ({len(rows)})")
                for row in rows:
                    print("  ", *row)


if __name__ == "__main__":
    main()
