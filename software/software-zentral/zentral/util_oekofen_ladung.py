import time

import numpy as np
from scipy.interpolate import LinearNDInterpolator  # type: ignore[import]


class InterpolatorInput:
    def __init__(self, brennernamen: str, temp_ein_C: float, temp_aus_C: float) -> None:
        self.brennernamen = brennernamen
        offset = 1.0
        lines = [
            # (x1, y1, x2, y2, value)
            (0, temp_ein_C, temp_aus_C - offset, temp_ein_C, 0),  # Einschalten
            (temp_aus_C, 100, temp_aus_C, temp_ein_C + offset, 100),  # Ausschalten
            (temp_aus_C - offset, temp_ein_C + offset, 0, 100, 50),  # 50% linie
            (0, 1, 1, 0, -100),
            (0, temp_ein_C - 11.0, 60, 18, -40),
            (temp_aus_C + 10.0, 100, 94, 43, 150),
            (90, 100, 100, 90, 180),
            (99, 100, 100, 99, 200),
        ]

        x: list[float] = []
        y: list[float] = []
        z: list[float] = []

        for x1, y1, x2, y2, value in lines:
            num_points = 50
            xi = np.linspace(x1, x2, num_points)
            yi = np.linspace(y1, y2, num_points)
            # Falls Linien vertikal oder horizontal sind
            if x1 == x2:  # vertikal
                yi = np.linspace(y1, y2, num_points)
                xi = np.full_like(yi, x1)
            elif y1 == y2:  # horizontal
                xi = np.linspace(x1, x2, num_points)
                yi = np.full_like(xi, y1)

            x.extend(xi)
            y.extend(yi)
            z.extend([value] * num_points)
        self.x = np.array(x)
        self.y = np.array(y)
        self.z = np.array(z)
        self.points = np.c_[x, y]

    def get_interpolator(self) -> LinearNDInterpolator:
        return LinearNDInterpolator(self.points, self.z)


class Interpolatoren:
    """ich waehle"""

    TPO_ein_A_C = 65.0
    "Einschalttemperatur erster Brenner, A"
    TPM_aus_A_C = 70.0
    "Ausschalttemperatur erster Brenner, A"
    TPO_ein_B_C = 60.0
    "Einschalttemperatur zweiter Brenner, B"
    TPM_aus_B_C = 65.0
    "Ausschalttemperatur zweiter Brenner, B"

    def __init__(self) -> None:
        self.oekofen_puffertemp_min_ein_TPO = self.TPO_ein_B_C
        self.oekofen_Abschaltueberhoehung_2 = self.TPO_ein_A_C - self.oekofen_puffertemp_min_ein_TPO
        self.oekofen_puffertemp_min_aus_TPM = self.TPM_aus_B_C - self.oekofen_Abschaltueberhoehung_2
        self.oekofen_Abschaltueberhoehung_1 = self.TPM_aus_A_C - self.oekofen_puffertemp_min_aus_TPM

        print(f"Einstellen bei Oekofen: oekofen_puffertemp_min_ein_TPO {self.oekofen_puffertemp_min_ein_TPO}")
        print(f"Einstellen bei Oekofen: oekofen_Abschaltueberhoehung_2 {self.oekofen_Abschaltueberhoehung_2}")
        print(f"Einstellen bei Oekofen: oekofen_puffertemp_min_aus_TPM {self.oekofen_puffertemp_min_aus_TPM}")
        print(f"Einstellen bei Oekofen: oekofen_Abschaltueberhoehung_1 {self.oekofen_Abschaltueberhoehung_1}")

    def _get_interpolator(self, brennernamen: str, temp_ein_C: float, temp_aus_C: float) -> InterpolatorInput:
        return InterpolatorInput(brennernamen=brennernamen, temp_ein_C=temp_ein_C, temp_aus_C=temp_aus_C)

    def get_interpolator_A(self) -> InterpolatorInput:
        return self._get_interpolator(brennernamen="brenner_A", temp_ein_C=self.TPO_ein_A_C, temp_aus_C=self.TPM_aus_A_C)

    def get_interpolator_B(self) -> InterpolatorInput:
        return self._get_interpolator(brennernamen="brenner_B", temp_ein_C=self.TPO_ein_B_C, temp_aus_C=self.TPM_aus_B_C)


def main() -> None:
    interpolatoren = Interpolatoren()

    start_s = time.time()
    ii = interpolatoren.get_interpolator_A()
    ip = ii.get_interpolator()
    print(f"Create interpolator within {time.time() - start_s:0.3f} s")

    start_s = time.time()
    for x in range(100):
        for y in range(100):
            _z = ip(float(x), float(y))
            # print(x, y, _z)
    print(f"10'000 interpolations within {time.time() - start_s:0.3f} s")

    # Lenovo T14s, i7 von Hans
    # Create interpolator within 0.003 s
    # 10'000 interpolations within 0.257 s

    # Rasperrypi 4
    # Create interpolator within 0.012 s
    # 10'000 interpolations within 1.566 s


if __name__ == "__main__":
    main()
