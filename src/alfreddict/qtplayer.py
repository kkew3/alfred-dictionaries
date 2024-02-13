import subprocess
import typing as ty
import sys

from alfreddict import utils


def play(path: ty.Optional[str]):
    """
    Play ``path`` using ``mpg123``, or QuickTime Player if ``mpg123`` is not
    found. If ``path`` can be evaluated to ``False``, do nothing.
    """
    if not path:
        return

    try:
        subprocess.run(['mpg123', path],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       check=True,
                       timeout=7)
        return
    except FileNotFoundError:
        pass

    applescript = '''\
on run argv
    set theFile to the first item of argv
    set theFile to POSIX file theFile
    tell application "QuickTime Player"
        set theAudio to open file theFile
        tell theAudio
            set theDuration to duration
            play
        end tell
        delay theDuration + 1
        close theAudio
        quit
    end tell
end run'''
    subprocess.run(utils.applescript_as_cmd(applescript, path), check=True)


def main():
    play(sys.argv[1])


if __name__ == '__main__':
    main()
