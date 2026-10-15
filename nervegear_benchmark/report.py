from html import escape

import numpy as np


def bar_chart(path, title, rows):
    maximum = max(value for _, value in rows) * 1.15
    height = 110 + len(rows) * 46
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" '
        f'viewBox="0 0 900 {height}" role="img" aria-label="{escape(title)}">',
        '<rect width="100%" height="100%" fill="#fff"/>',
        '<g font-family="Arial,sans-serif" fill="#182637">',
        f'<text x="24" y="34" font-size="21">{escape(title)}</text>',
        '<text x="24" y="60" font-size="14">Macro recording MAE in degrees; '
        "one person, one session</text>",
    ]
    for i, (name, value) in enumerate(rows):
        y = 86 + i * 46
        width = value / max(maximum, 1e-9) * 560
        parts.extend(
            [
                f'<text x="24" y="{y + 19}" font-size="15">{escape(name)}</text>',
                f'<rect x="230" y="{y}" width="{width:.2f}" height="28" fill="#2563a6" rx="3"/>',
                f'<text x="{240 + width:.2f}" y="{y + 19}" font-size="15">{value:.2f}</text>',
            ]
        )
    parts.append("</g></svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_report(summary, output):
    degrees = 180 / np.pi
    clean = summary["test"]["clean"]["aggregate"]["macro_mae_rad"]
    rows = [
        (f"Train {name}", r["aggregate"]["macro_mae_rad"] * degrees)
        for name, r in summary["baselines"].items()
    ]
    rows += [
        (f"Ridge {r['history'] / 2:g} ms", r["aggregate"]["macro_mae_rad"] * degrees)
        for r in summary["history_comparisons"]
    ]
    bar_chart(output / "accuracy.svg", "Held-out recording accuracy", rows)
    robustness = [
        (name, r["aggregate"]["macro_mae_rad"] * degrees) for name, r in summary["test"].items()
    ]
    bar_chart(output / "robustness.svg", "Synthetic input sensitivity", robustness)
    delay = [
        (f"{name} ms delay", r["aggregate"]["macro_mae_rad"] * degrees)
        for name, r in summary["delayed_outputs"].items()
    ]
    bar_chart(output / "delay.svg", "Delayed prediction sensitivity", delay)
    selected = summary["selection"]
    lines = [
        "# CPU EMG pilot run",
        "",
        summary["scope"],
        "",
        f"Validation selected {selected['history'] / 2:g} ms history and "
        f"ridge alpha {selected['alpha']}. Test macro MAE: {clean:.6f} rad "
        f"({clean * degrees:.3f} degrees).",
        "",
        "| Method | Test macro MAE (degrees) |",
        "| --- | ---: |",
    ]
    lines += [f"| {name} | {value:.3f} |" for name, value in rows]
    lines += [
        "",
        "![Accuracy](accuracy.svg)",
        "",
        "![Synthetic sensitivity](robustness.svg)",
        "",
        "![Delayed predictions](delay.svg)",
        "",
        "Read summary.json for per-recording and per-joint errors, coverage, validation "
        "candidates, five timing passes, and resource use.",
        "",
        "History means past input support, not mandatory buffering. No future samples, "
        "reference-pose input, or test-label calibration enter fitting. "
        "Timing excludes I/O and replay scheduling and does not measure sensor-to-percept latency.",
        "",
        "This custom pilot is not an official emg2pose benchmark. It cannot establish "
        "new-user or new-session performance, live control, biological robustness, perception, "
        "or full-dive capability. Synthetic perturbations and delayed outputs are offline "
        "diagnostics. No human feedback loop is modeled.",
        "",
        "Data attribution: emg2pose, Meta and its authors, upstream commit "
        f"{summary['source_commit']}. See docs/datasets/emg2pose.md for source and license terms.",
        "No source recordings or per-sample predictions are included in this report.",
        "",
    ]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
