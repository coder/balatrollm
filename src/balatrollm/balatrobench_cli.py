"""BalatroLLM Benchmark CLI module."""

import sys
from pathlib import Path

from . import __version__
from .benchmark import BenchmarkAnalyzer


def main() -> None:
    """Main CLI entry point for balatrobench.

    Parses command line arguments and runs benchmark analysis for a single version.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze BalatroLLM runs and generate benchmark leaderboards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Mutually exclusive group for analysis type
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--models",
        action="store_true",
        help="Analyze by models (compare models within strategies)",
    )
    group.add_argument(
        "--strategies",
        action="store_true",
        help="Analyze by strategies (compare strategies for each model)",
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help=f"Input directory with run data (default: runs/v{__version__})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=f"Output directory for benchmark results (default: benchmarks/[models|strategies]/v{__version__})",
    )
    parser.add_argument(
        "--avif",
        action="store_true",
        help="Convert PNG screenshots to AVIF format after analysis",
    )

    args = parser.parse_args()

    # Set default input directory
    if args.input_dir is None:
        args.input_dir = Path(f"runs/v{__version__}").resolve()
    else:
        args.input_dir = args.input_dir.resolve()

    # Determine output directory based on flag
    if args.output_dir is None:
        if args.models:
            args.output_dir = Path(f"benchmarks/models/v{__version__}").resolve()
        else:  # args.strategies
            args.output_dir = Path(f"benchmarks/strategies/v{__version__}").resolve()
    else:
        args.output_dir = args.output_dir.resolve()

    try:
        analyzer = BenchmarkAnalyzer(args.input_dir, args.output_dir)

        if args.models:
            analyzer.analyze_version_by_models(args.input_dir)
        else:  # args.strategies
            analyzer.analyze_version_by_strategies(args.input_dir)

        # Convert PNGs to AVIF if requested
        if args.avif:
            print("Converting PNG screenshots to AVIF format...")
            analyzer.convert_pngs_to_avif(args.output_dir)

        # Generate manifest.json in the base benchmark directory
        manifest_base_dir = args.output_dir.parent
        analyzer.generate_manifest(manifest_base_dir, __version__)

        print(f"Benchmark analysis complete. Results saved to {args.output_dir}")
        print(f"Manifest updated at {manifest_base_dir / 'manifest.json'}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Benchmark analysis failed: {e}")
        sys.exit(1)
