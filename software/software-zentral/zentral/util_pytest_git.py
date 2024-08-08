import pathlib
import subprocess


def assert_git_unchanged(filename_png: pathlib.Path):
    try:
        subprocess.run(
            args=[
                "git",
                "diff",
                "--exit-code",
                str(filename_png),
            ],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise AssertionError(f"{filename_png}:\nstderr:{e.stderr}\nstdout:{e.stdout}\nExit code {e.returncode}: If this is 1, then the file has changed.") from e
