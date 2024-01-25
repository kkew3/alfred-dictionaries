import subprocess
import typing as ty
import sys

from alfreddict import utils


def play(path: ty.Optional[str]):
    """
    Play ``path`` using QuickTime Player. If ``path`` can be evaluated to
    ``False``, do nothing.
    """
    applescript = '''\
on run argv
    set theFile to the first item of argv
    if theFile = "" then
        return
    end if
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
    subprocess.run(
        utils.applescript_as_cmd(applescript, path or ''), check=True)


def main():
    play(sys.argv[1])


if __name__ == '__main__':
    main()
