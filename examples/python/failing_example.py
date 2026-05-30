#!/usr/bin/env python3
"""
Failing example using the generic LineageTracker.

This script intentionally raises an exception during processing so that
the tracker emits a FAIL event to Marquez.
"""

import os
import pandas as pd

from lineage_tracker import LineageTracker, infer_schema_from_dataframe


DATA_DIR = "../../data"
MARQUEZ_URL = os.getenv("MARQUEZ_URL", "http://localhost:5050")


def main() -> None:
    tracker = LineageTracker(
        marquez_url=MARQUEZ_URL,
        namespace="failure-example",
        job_name="data-processor-fail",
        job_description="Intentional failure demo to emit FAIL lineage event",
    )

    print("=" * 64)
    print("Failing Lineage Tracking Example")
    print("=" * 64)
    print("This script is expected to fail and emit a FAIL event.\n")

    os.makedirs(DATA_DIR, exist_ok=True)

    input_file = os.path.join(DATA_DIR, "products_failure_input.csv")
    output_file = os.path.join(DATA_DIR, "products_failure_output.csv")

    df_input = pd.DataFrame(
        {
            "product_id": [1, 2, 3],
            "name": ["Laptop", "Mouse", "Keyboard"],
            "price": [1200, 25, 75],
        }
    )
    df_input.to_csv(input_file, index=False)

    with tracker.track_run() as run:
        run.add_input(
            name="products_failure_input.csv",
            uri=f"file://{os.path.abspath(input_file)}",
            schema=infer_schema_from_dataframe(df_input),
        )

        # Simulate an application bug during transformation.
        raise RuntimeError("Intentional pipeline failure for lineage demo")

        # This line is intentionally unreachable.
        df_input.to_csv(output_file, index=False)


if __name__ == "__main__":
    main()
