"""Generate distribution plots from test packet CSV data."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 8)


def plot_distributions():
    """Generate distribution plots from CSV files."""
    csv_dir = Path(__file__).parent / "output" / "csv"
    plots_dir = Path(__file__).parent / "output" / "plots"
    plots_dir.mkdir(exist_ok=True)

    # Uint16 distribution from visualization dataset
    csv_file = csv_dir / "viz_uint16_large.csv"
    if csv_file.exists():
        df = pd.read_csv(csv_file)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle("uint16 Random Distribution (5,000 packets)", fontsize=16, y=0.995)

        # Histogram
        axes[0, 0].hist(
            df["uint16_value"],
            bins=100,
            color="steelblue",
            alpha=0.7,
            edgecolor="black",
        )
        axes[0, 0].set_xlabel("Value")
        axes[0, 0].set_ylabel("Frequency")
        axes[0, 0].set_title("Histogram (100 bins)")
        axes[0, 0].axvline(
            df["uint16_value"].mean(),
            color="red",
            linestyle="--",
            linewidth=2,
            label=f'Mean: {df["uint16_value"].mean():.1f}',
        )
        axes[0, 0].legend()

        # Box plot
        axes[0, 1].boxplot(df["uint16_value"], vert=True)
        axes[0, 1].set_ylabel("Value")
        axes[0, 1].set_title("Box Plot")
        axes[0, 1].set_xticklabels(["uint16 values"])

        # Cumulative distribution
        sorted_data = df["uint16_value"].sort_values()
        axes[1, 0].plot(
            sorted_data.values,
            range(len(sorted_data)),
            color="steelblue",
            linewidth=2,
        )
        axes[1, 0].set_xlabel("Value")
        axes[1, 0].set_ylabel("Cumulative Count")
        axes[1, 0].set_title("Cumulative Distribution Function")
        axes[1, 0].grid(True, alpha=0.3)

        # Statistics table
        stats = df["uint16_value"].describe()
        axes[1, 1].axis("off")
        stats_text = f"""
Statistics Summary:
━━━━━━━━━━━━━━━━━━━━
Count:    {stats['count']:.0f}
Mean:     {stats['mean']:.2f}
Std Dev:  {stats['std']:.2f}
Min:      {stats['min']:.0f}
25%:      {stats['25%']:.0f}
Median:   {stats['50%']:.0f}
75%:      {stats['75%']:.0f}
Max:      {stats['max']:.0f}

Expected (uniform):
Mean:     32767.5
Range:    0 - 65535
"""
        axes[1, 1].text(
            0.1,
            0.5,
            stats_text,
            fontsize=12,
            verticalalignment="center",
            fontfamily="monospace",
        )

        plt.tight_layout()
        output_file = plots_dir / "uint16_distribution.png"
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        print(f"Saved: {output_file}")
        plt.close()

    # Large array random distribution (old test data, kept for compatibility)
    csv_file = csv_dir / "large_array_random.csv"
    if csv_file.exists():
        df = pd.read_csv(csv_file)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(
            "Random Data Distribution (10,000 uint16 values)", fontsize=16, y=0.995
        )

        # Histogram
        axes[0, 0].hist(df["large_data_value"], bins=100, color="steelblue", alpha=0.7)
        axes[0, 0].set_xlabel("Value")
        axes[0, 0].set_ylabel("Frequency")
        axes[0, 0].set_title("Histogram (100 bins)")
        axes[0, 0].axvline(
            df["large_data_value"].mean(),
            color="red",
            linestyle="--",
            label=f'Mean: {df["large_data_value"].mean():.1f}',
        )
        axes[0, 0].legend()

        # Box plot
        axes[0, 1].boxplot(df["large_data_value"], vert=True)
        axes[0, 1].set_ylabel("Value")
        axes[0, 1].set_title("Box Plot")
        axes[0, 1].set_xticklabels(["uint16 values"])

        # Cumulative distribution
        sorted_data = df["large_data_value"].sort_values()
        axes[1, 0].plot(
            sorted_data.values,
            range(len(sorted_data)),
            color="steelblue",
            linewidth=2,
        )
        axes[1, 0].set_xlabel("Value")
        axes[1, 0].set_ylabel("Cumulative Count")
        axes[1, 0].set_title("Cumulative Distribution Function")
        axes[1, 0].grid(True, alpha=0.3)

        # Statistics table
        stats = df["large_data_value"].describe()
        axes[1, 1].axis("off")
        stats_text = f"""
Statistics Summary:
━━━━━━━━━━━━━━━━━━━━
Count:    {stats['count']:.0f}
Mean:     {stats['mean']:.2f}
Std Dev:  {stats['std']:.2f}
Min:      {stats['min']:.0f}
25%:      {stats['25%']:.0f}
Median:   {stats['50%']:.0f}
75%:      {stats['75%']:.0f}
Max:      {stats['max']:.0f}

Expected (uniform):
Mean:     32767.5
Range:    0 - 65535
"""
        axes[1, 1].text(
            0.1,
            0.5,
            stats_text,
            fontsize=12,
            verticalalignment="center",
            fontfamily="monospace",
        )

        plt.tight_layout()
        output_file = plots_dir / "uint16_distribution.png"
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        print(f"Saved: {output_file}")
        plt.close()

    # Signed integers distribution from visualization dataset
    csv_file = csv_dir / "viz_signed_integers_large.csv"
    if csv_file.exists():
        df = pd.read_csv(csv_file)

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle("Signed Integer Random Distributions", fontsize=16)

        # int8
        axes[0].hist(df["int8_val"], bins=50, color="coral", alpha=0.7)
        axes[0].set_xlabel("Value")
        axes[0].set_ylabel("Frequency")
        axes[0].set_title(f"int8 (-128 to 127)\nMean: {df['int8_val'].mean():.2f}")
        axes[0].axvline(0, color="black", linestyle="--", alpha=0.5, label="Zero")
        axes[0].legend()

        # int16
        axes[1].hist(df["int16_val"], bins=50, color="lightgreen", alpha=0.7)
        axes[1].set_xlabel("Value")
        axes[1].set_ylabel("Frequency")
        axes[1].set_title(
            f"int16 (-32768 to 32767)\nMean: {df['int16_val'].mean():.2f}"
        )
        axes[1].axvline(0, color="black", linestyle="--", alpha=0.5, label="Zero")
        axes[1].legend()

        # int32
        axes[2].hist(df["int32_val"], bins=50, color="plum", alpha=0.7)
        axes[2].set_xlabel("Value")
        axes[2].set_ylabel("Frequency")
        axes[2].set_title(f"int32 (-2B to 2B)\nMean: {df['int32_val'].mean():.0f}")
        axes[2].axvline(0, color="black", linestyle="--", alpha=0.5, label="Zero")
        axes[2].legend()

        plt.tight_layout()
        output_file = plots_dir / "signed_integers_distribution.png"
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        print(f"Saved: {output_file}")
        plt.close()

    # Float distribution from visualization dataset
    csv_file = csv_dir / "viz_float_large.csv"
    if csv_file.exists():
        df = pd.read_csv(csv_file)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(
            "float32 Random Distribution (2,000 packets)", fontsize=16, y=0.995
        )

        # Histogram
        axes[0, 0].hist(
            df["float_val"],
            bins=100,
            color="steelblue",
            alpha=0.7,
            edgecolor="black",
        )
        axes[0, 0].set_xlabel("Value")
        axes[0, 0].set_ylabel("Frequency")
        axes[0, 0].set_title("Histogram (100 bins)")
        axes[0, 0].axvline(
            df["float_val"].mean(),
            color="red",
            linestyle="--",
            linewidth=2,
            label=f'Mean: {df["float_val"].mean():.2f}',
        )
        axes[0, 0].legend()

        # Box plot
        axes[0, 1].boxplot(df["float_val"], vert=True)
        axes[0, 1].set_ylabel("Value")
        axes[0, 1].set_title("Box Plot")
        axes[0, 1].set_xticklabels(["float32 values"])

        # Cumulative distribution
        sorted_data = df["float_val"].sort_values()
        axes[1, 0].plot(
            sorted_data.values,
            range(len(sorted_data)),
            color="steelblue",
            linewidth=2,
        )
        axes[1, 0].set_xlabel("Value")
        axes[1, 0].set_ylabel("Cumulative Count")
        axes[1, 0].set_title("Cumulative Distribution Function")
        axes[1, 0].grid(True, alpha=0.3)

        # Statistics table
        stats = df["float_val"].describe()
        axes[1, 1].axis("off")
        stats_text = f"""
Statistics Summary:
━━━━━━━━━━━━━━━━━━━━
Count:    {stats['count']:.0f}
Mean:     {stats['mean']:.2f}
Std Dev:  {stats['std']:.2f}
Min:      {stats['min']:.2f}
25%:      {stats['25%']:.2f}
Median:   {stats['50%']:.2f}
75%:      {stats['75%']:.2f}
Max:      {stats['max']:.2f}

Expected (uniform):
Mean:     0.0
Range:    -1000 to 1000
"""
        axes[1, 1].text(
            0.1,
            0.5,
            stats_text,
            fontsize=12,
            verticalalignment="center",
            fontfamily="monospace",
        )

        plt.tight_layout()
        output_file = plots_dir / "float32_distribution.png"
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        print(f"Saved: {output_file}")
        plt.close()

    print(f"\nPlots saved to: {plots_dir}")


if __name__ == "__main__":
    plot_distributions()
