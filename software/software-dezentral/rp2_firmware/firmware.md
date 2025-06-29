# Micropython Firmware dezentral

## Actual Firmware

* https://github.com/hmaerki/fork_micropython/blob/hmaerki/XTAL/README_hans.md
* Commit `b18ff701a6b8dee7b2870293053510fd61314032`
* MicroPython v1.22.2-4.gf1d21e75a.dirty on 2024-02-25; Raspberry Pi Pico (slow XTAL) with RP2040

## Backup of the branch `hmaerki/XTAL`

Commit `8cd15829e293f01dae91b6a2d4a995bfaeca887b all: Bump version to 1.22.2.` is where my changes started.
Commit `f1d21e75ac792725c0b77a838059bb92d1f00f01 v1.22` should be `firmware.uf2` in this directory!

```bash
cd ~/gits/fork_micropython
git checkout hmaerki/XTAL
git format-patch 8cd15829e293f01dae91b6a2d4a995bfaeca887b..hmaerki/XTAL
```

# Summary

To recreate `firmware.uf2`:
* clone https://github.com/micropython/micropython
* checkout `8cd15829e293f01dae91b6a2d4a995bfaeca887b`
* Apply theses patches:
  * 0001-PICO_XOSC_STARTUP_DELAY_MULTIPLIER-64.patch
  * 0002-16-Giga-Flash.patch
  * 0003-clean-rebuild.patch
* Build the firmware