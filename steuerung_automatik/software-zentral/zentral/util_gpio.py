"""
https://www.elektronik-kompendium.de/sites/raspberry-pi/2202101.htm
https://kofler.info/gpio-reloaded-ii-bash/


When a modbus error occurs, during the subsequent sleep of ~50ms, a trigger pin is held high.

  gpio_modbus_error = Gpio("20")
  gpio_modbus_no_response = Gpio("21")

These are the pin assignements: https://www.elektronik-kompendium.de/sites/raspberry-pi/1907101.htm
"""

import pathlib
import subprocess
import typing

SCOPE_TRIGGER_ENABLED = False


def is_raspberrypi():
    if not SCOPE_TRIGGER_ENABLED:
        return False

    filename_model = pathlib.Path("/sys/firmware/devicetree/base/model")
    if not filename_model.exists():
        return False
    model = filename_model.read_text()
    return "raspberry pi" in model.lower()


class Gpio:
    def __init__(self, nr: str):
        self.nr = nr
        self.is_raspberry = is_raspberrypi()
        self.args_on = ["pinctrl", "set", str(nr), "op", "dh"]
        self.args_off = ["pinctrl", "set", str(nr), "op", "dl"]
        self.set_value(on=False)

    def _run(self, args: typing.List[str]) -> None:
        assert isinstance(args, list)
        cmd = " ".join(args)
        # print(f"RUNNING: {cmd}")
        proc = subprocess.run(args, capture_output=True)
        if proc.returncode == 0:
            return

        print(f"  returncode={proc.returncode}")
        print(f"  stdout={proc.stdout!s}")
        print(f"  stderr={proc.stderr!s}")
        raise Exception(f"{cmd}: {proc.returncode}: {proc.stderr}")

    def set_value(self, on: bool) -> None:
        if not self.is_raspberry:
            return

        self._run(self.args_on if on else self.args_off)

    def __enter__(self):
        self.set_value(on=True)
        return self

    def __exit__(self, type, value, traceback):
        self.set_value(on=False)


class ScopeTrigger:
    def __init__(self):
        self.modbus_error = Gpio("20")
        self.modbus_no_response = Gpio("21")
