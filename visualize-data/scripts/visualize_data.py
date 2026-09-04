#!/usr/bin/env python3
"""Zero-install launcher for the visualize-data CLI."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

from visualize_data.cli import main  # noqa: E402

raise SystemExit(main())
