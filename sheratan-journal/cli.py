import argparse
import glob
import os
from src.pipeline.ingest import ingest_many


def main():
    parser = argparse.ArgumentParser(prog="sheratan-journal")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ing = sub.add_parser("ingest", help="Ingest PDF/HTML files")
    p_ing.add_argument("--input", required=True, help="File path or glob, e.g. data/in/*.pdf")
    p_ing.add_argument("--week", type=int, required=True, help="ISO week number (1-53)")
    p_ing.add_argument("--year", type=int, required=True, help="Year")
    p_ing.add_argument("--outdir", default="data/out", help="Output directory root")
    p_ing.add_argument("--dry-run", action="store_true", help="Do not write final structured output")
    p_ing.add_argument("--max-chars", type=int, default=120000, help="Max chars sent to LLM")

    args = parser.parse_args()

    # Expand glob or single path
    matches = sorted(glob.glob(args.input))
    if not matches:
        if os.path.exists(args.input):
            matches = [args.input]
        else:
            raise SystemExit(f"No files matched input: {args.input}")

    ingest_many(
        input_files=matches,
        week=args.week,
        year=args.year,
        out_root=args.outdir,
        dry_run=args.dry_run,
        max_chars=args.max_chars,
    )


if __name__ == "__main__":
    main()
