import matplotlib.pyplot as plt
import numpy as np

from zentral.util_oekofen_ladung import InterpolatorInput, Interpolatoren


def plot1(t: Interpolatoren) -> None:
    assert isinstance(t, Interpolatoren)
    labels = ["Brenner A", "Brenner B"]
    bottoms = [t.TPO_ein_A_C, t.TPO_ein_B_C]  # Untere Grenze der Balken
    heights = [t.TPM_aus_A_C - t.TPO_ein_A_C, t.TPM_aus_B_C - t.TPO_ein_B_C]  # Höhe der Balken
    plt.bar(labels, heights, bottom=bottoms, width=0.4)
    plt.ylim(50, 80)
    plt.ylabel("Temperatur C")
    plt.title("Ein- und Auschalttemperaturen erster brenner_A und zweiter brenner_B")
    plt.grid(axis="y", linestyle="--", linewidth=0.7, alpha=0.7)
    plt.show()


def plot2(interpolator_input: InterpolatorInput) -> None:
    assert isinstance(interpolator_input, InterpolatorInput)
    brennernamen = interpolator_input.brennernamen
    interpolator = interpolator_input.get_interpolator()
    x = interpolator_input.x
    y = interpolator_input.y

    X = np.linspace(min(x) - 5, max(x) + 5, 100)
    Y = np.linspace(min(y) - 5, max(y) + 5, 100)
    X, Y = np.meshgrid(X, Y)
    Z = interpolator(X, Y)
    levels = np.arange(-100, 200, 10)

    plt.figure(figsize=(10, 6))
    plt.title(f"Ladung Speicher Zentral, {brennernamen}, unter 0: schaltet ein, ueber 100: schaltet aus")
    plt.imshow(Z, extent=(min(x) - 5, max(x) + 5, min(y) - 5, max(y) + 5), origin="lower", cmap="viridis", aspect="auto")
    plt.colorbar(label="Ladung")
    contour = plt.contour(X, Y, Z, levels=levels, colors="black", linewidths=0.8)
    plt.clabel(contour, inline=True, fontsize=8, fmt="%1.1f", colors="black")
    plt.scatter(x, y, color="red", edgecolor="k", s=10, zorder=5)
    plt.xlabel("TPM_C")
    plt.ylabel("TPO_C")
    plt.plot([0, 100], [0, 100], color="red", linewidth=1)
    plt.fill_between(x=np.linspace(0, 100, 500), y1=0, y2=np.linspace(0, 100, 500), where=(np.linspace(0, 100, 500) <= np.linspace(0, 100, 500)), facecolor="none", hatch=("\\"), edgecolor="red", alpha=1, zorder=4)
    plt.show()


def main() -> None:
    interpolatoren = Interpolatoren()

    plot1(interpolatoren)

    plot2(interpolatoren.get_interpolator_A())
    plot2(interpolatoren.get_interpolator_B())


if __name__ == "__main__":
    main()
