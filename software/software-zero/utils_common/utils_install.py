import subprocess
import typing


def run(args: typing.List[str]) -> None:
    assert isinstance(args, list)
    cmd = " ".join(args)
    print(f"RUNNING: {cmd}")
    proc = subprocess.run(args, capture_output=True)
    if proc.returncode != 0:
        print(f"  returncode={proc.returncode}")
        print(f"  stdout={proc.stdout}")
        print(f"  stderr={proc.stderr}")
        raise Exception(f"{cmd}: {proc.returncode}: {proc.stderr}")
