import argparse
import os
import sys
import threading
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run the software-only EMG research commands")
    parser.add_argument("command", choices=["run", "diagnose", "calibrate", "align", "history"])
    parser.add_argument("--manifest", type=Path, default=Path("research/emg2pose/pilot-v1.json"))
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--calibration-protocol", type=Path)
    parser.add_argument("--alignment-protocol", type=Path)
    parser.add_argument("--history-protocol", type=Path)
    args = parser.parse_args()
    if args.calibration_protocol is not None and args.command != "calibrate":
        parser.error("--calibration-protocol is only valid for calibrate")
    if args.alignment_protocol is not None and args.command != "align":
        parser.error("--alignment-protocol is only valid for align")
    if args.history_protocol is not None and args.command != "history":
        parser.error("--history-protocol is only valid for history")
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
        if args.command == "history":
            from .history import run

            run(
                args.manifest,
                args.data_dir,
                args.output,
                args.history_protocol or Path("research/emg2pose/history-v1.json"),
            )
        elif args.command == "align":
            from .alignment import run

            run(
                args.manifest,
                args.data_dir,
                args.output,
                args.alignment_protocol or Path("research/emg2pose/alignment-v1.json"),
            )
        elif args.command == "calibrate":
            from .calibration import run

            run(
                args.manifest,
                args.data_dir,
                args.output,
                args.calibration_protocol or Path("research/emg2pose/calibration-v1.json"),
            )
        elif args.command == "diagnose":
            from .diagnostics import run

            run(args.manifest, args.data_dir, args.output)
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
