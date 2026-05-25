import io
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")  # Non-GUI backend, required for Flask
import matplotlib.pyplot as plt


def generate_category_chart(answers) -> bytes:
    """
    Generates a horizontal bar chart showing accuracy percentage by category.
    Receives a list of Answer objects. Returns PNG bytes.
    """
    totals = defaultdict(int)
    correct = defaultdict(int)

    for a in answers:
        cat = a.category or "Other"
        totals[cat] += 1
        if a.is_correct:
            correct[cat] += 1

    if not totals:
        return _empty_chart()

    categories = list(totals.keys())
    accuracy = [correct[c] / totals[c] * 100 for c in categories]

    # Colorful/arcade palette
    colors = ["#FF6B6B", "#FFD93D", "#6BCB77", "#4ECDC4",
              "#C77DFF", "#FF9A3C", "#F72585", "#4D96FF"]

    fig, ax = plt.subplots(figsize=(8, max(3, len(categories) * 0.7)))
    fig.patch.set_facecolor("#0f0a1e")
    ax.set_facecolor("#1a1040")

    bars = ax.barh(
        categories,
        accuracy,
        color=[colors[i % len(colors)] for i in range(len(categories))],
        edgecolor="none",
        height=0.55,
    )

    # Percentage label at the end of each bar
    for bar, val in zip(bars, accuracy):
        ax.text(
            min(val + 2, 92),
            bar.get_y() + bar.get_height() / 2,
            f"{val:.0f}%",
            va="center",
            color="white",
            fontsize=9,
            fontweight="bold",
        )

    ax.set_xlim(0, 100)
    ax.set_xlabel("% correct", color="#94a3b8", fontsize=9)
    ax.tick_params(colors="#94a3b8", labelsize=8)
    ax.spines[:].set_visible(False)
    ax.set_title("Accuracy by Category", color="white", fontsize=11, pad=10)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _empty_chart() -> bytes:
    """Returns a placeholder PNG when there is no data yet."""
    fig, ax = plt.subplots(figsize=(6, 2))
    fig.patch.set_facecolor("#0f0a1e")
    ax.set_facecolor("#1a1040")
    ax.text(0.5, 0.5, "No data yet — play some games first!",
            ha="center", va="center", color="#94a3b8",
            fontsize=11, transform=ax.transAxes)
    ax.axis("off")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()