#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path


def extract_rows(data: dict):
    rows = []
    for query in data.get("queries", []):
        stage_id = query.get("query_id")
        for tb in query.get("thread_blocks", []):
            rows.append(
                {
                    "stage_id": stage_id,
                    "thread_block_id": tb.get("thread_block_id"),
                    "optimal_dop": tb.get("optimal_dop"),
                }
            )
    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Extract stage_id/query_id, thread_block_id and optimal_dop from pipeline_optimization.json"
    )
    parser.add_argument(
        "-i",
        "--input",
        default="output/tpch/optimization_results/pipeline_optimization.json",
        help="Path to input JSON file",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output/tpch/optimization_results/stage_threadblock_optimal_dop.csv",
        help="Path to output CSV file",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    rows = extract_rows(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["stage_id", "thread_block_id", "optimal_dop"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Extracted {len(rows)} rows -> {output_path}")


if __name__ == "__main__":
    main()
