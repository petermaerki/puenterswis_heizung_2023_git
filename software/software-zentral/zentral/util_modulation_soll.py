from __future__ import annotations

import dataclasses

_LIST_MODULATION_PROZENT = [0, 30, 65, 100]


@dataclasses.dataclass
class ModulationBrenner:
    idx: int
    idx_modulation: int

    @staticmethod
    def get_idx(modulation: int) -> int:
        for idx, m in enumerate(_LIST_MODULATION_PROZENT):
            if m == modulation:
                return idx
        raise ValueError(f"Modulation {modulation} ist nicht in {_LIST_MODULATION_PROZENT}!")

    def set_max(self) -> None:
        self.idx_modulation = len(_LIST_MODULATION_PROZENT) - 1

    @property
    def short(self) -> str:
        return f"{self.modulation_prozent:3d}"

    @property
    def is_off(self) -> bool:
        return self.idx_modulation <= 0

    @property
    def is_on(self) -> bool:
        return self.idx_modulation > 0

    @property
    def is_min(self) -> bool:
        return self.idx_modulation == 1

    @property
    def is_max(self) -> bool:
        return self.idx_modulation >= len(_LIST_MODULATION_PROZENT) - 1

    @property
    def is_over_min(self) -> bool:
        return self.idx_modulation > 1

    @property
    def modulation_prozent(self) -> int:
        return _LIST_MODULATION_PROZENT[self.idx_modulation]

    def erhoehen(self) -> None:
        self.idx_modulation += 1
        assert 0 <= self.idx_modulation < len(_LIST_MODULATION_PROZENT)

    def absenken(self) -> None:
        self.idx_modulation -= 1
        assert 0 <= self.idx_modulation < len(_LIST_MODULATION_PROZENT)


@dataclasses.dataclass
class ZweiBrenner:
    zwei_brenner: tuple[ModulationBrenner, ModulationBrenner]

    @property
    def short(self) -> str:
        return ",".join([b.short for b in self.zwei_brenner])

    def on_but_not_max(self) -> list[ModulationBrenner]:
        return [b for b in self.zwei_brenner if b.is_on and not b.is_max]

    def off(self) -> list[ModulationBrenner]:
        return [b for b in self.zwei_brenner if b.is_off]

    def on(self) -> list[ModulationBrenner]:
        return [b for b in self.zwei_brenner if b.is_on]

    def min(self) -> list[ModulationBrenner]:
        return [b for b in self.zwei_brenner if b.is_min]

    def is_over_min(self) -> list[ModulationBrenner]:
        return [b for b in self.zwei_brenner if b.is_over_min]


class ModulationSoll:
    WARTEZEIT_OFEN_EIN_MIN = 40
    WARTEZEIT_OFEN_AUS_MIN = 30
    WARTEZEIT_OFEN_MODULIEREN_MIN = 15
    WARTEZEIT_OFEN_NICHTS_MIN = 1

    def __init__(self, modulation0: int = 0, modulation1: int = 1) -> None:
        self.zwei_brenner = ZweiBrenner(
            (
                ModulationBrenner(idx=0, idx_modulation=ModulationBrenner.get_idx(modulation0)),
                ModulationBrenner(idx=1, idx_modulation=ModulationBrenner.get_idx(modulation1)),
            )
        )
        self.wartezeit_min: int = 0

    @property
    def short(self) -> str:
        return f"{ self.zwei_brenner.short},{self.wartezeit_min:2d}min"

    def tick(self, ladung_prozent: float, manual_mode: bool) -> None:
        if manual_mode:
            # Temporaere einfache Lösung
            # Langfristig
            #   Zustand der Brenner abfragen und 'zwei_brenner' sinnvoll
            #   initialisieren.
            self.zwei_brenner.zwei_brenner[0].set_max()
            self.zwei_brenner.zwei_brenner[1].set_max()
            return

        self.wartezeit_min = self.WARTEZEIT_OFEN_NICHTS_MIN
        if ladung_prozent < 5.0:
            self._erhoehen(ladung_prozent=ladung_prozent)
            return
        if ladung_prozent > 30.0:
            self._reduzieren(ladung_prozent=ladung_prozent)

    def _erhoehen(self, ladung_prozent: float) -> None:
        list_brenner_on = self.zwei_brenner.on_but_not_max()
        if len(list_brenner_on) >= 1:
            # Brenner moduliert bereits
            list_brenner_on[0].erhoehen()
            self.wartezeit_min = self.WARTEZEIT_OFEN_MODULIEREN_MIN
            return

        list_brenner_off = self.zwei_brenner.off()
        if len(list_brenner_off) > 0:
            if ladung_prozent < 0:
                # Brenner einschalten
                list_brenner_off[0].erhoehen()
                self.wartezeit_min = self.WARTEZEIT_OFEN_EIN_MIN
                return

    def _reduzieren(self, ladung_prozent: float) -> None:
        list_brenner_is_over_min = self.zwei_brenner.is_over_min()
        if len(list_brenner_is_over_min) >= 1:
            # Brenner moduliert bereits
            list_brenner_is_over_min[0].absenken()
            self.wartezeit_min = self.WARTEZEIT_OFEN_MODULIEREN_MIN
            return

        list_brenner_on = self.zwei_brenner.on()
        if len(list_brenner_on) == 0:
            # Beide Brenner sind bereits aus
            return

        # Mindestens ein Brenner ist an
        if ladung_prozent > 100.0:
            # Brenner ausschalten
            list_brenner_on[0].absenken()
            self.wartezeit_min = self.WARTEZEIT_OFEN_AUS_MIN
            return

        if len(list_brenner_on) == 2:
            if ladung_prozent >= 95.0:
                # Brenner ausschalten
                list_brenner_on[0].absenken()
                self.wartezeit_min = self.WARTEZEIT_OFEN_AUS_MIN
                return
