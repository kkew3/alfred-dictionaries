on run argv
	set theFilename to the first item of argv
	if theFilename = "" then
		return
	end if
	set theFilename to POSIX file theFilename
	tell application "QuickTime Player"
		set theAudio to open file theFilename
		tell theAudio
			set theDuration to duration
			play
		end tell
		delay theDuration + 1
		close theAudio
		quit
	end tell
end run
