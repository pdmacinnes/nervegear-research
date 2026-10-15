import argparse
import os
import sys
import threading
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run the software-only EMG research commands")
    parser.add_argument("command", choices=["run", "diagnose"])
    parser.add_argument("--manifest", type=Path, default=Path("research/emg2pose/pilot-v1.json"))
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for key in [
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OMP_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ]:
        os.environ[key] = "2"

    def timeout():
        print("Benchmark stopped at the 15-minute wall-clock limit", file=sys.stderr, flush=True)
        os._exit(124)

    watchdog = threading.Timer(900, timeout)
    watchdog.daemon = True
    watchdog.start()
    try:
        if args.command == "diagnose":
            from .diagnostics import run
        else:
            from .pipeline import run

        run(args.manifest, args.data_dir, args.output)
    except (OSError, ValueError, KeyError) as error:
        print(f"Benchmark failed: {error}", file=sys.stderr)
        return 1
    finally:
        watchdog.cancel()
    return 0


if __name__ == "__main__":
    sys.exit(main())
