from __future__ import annotations

import argparse

from app.loaders import load_folder
from app.rag import ingest_docs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="要入库的目录（递归扫描 txt/md/pdf/docx）")
    ap.add_argument("--collection", default="default")
    args = ap.parse_args()

    docs = load_folder(args.path)
    res = ingest_docs(docs=docs, collection=args.collection)
    print(f"collection={args.collection} added_chunks={res.added_chunks}")


if __name__ == "__main__":
    main()

