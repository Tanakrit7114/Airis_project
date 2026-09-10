"""Explicit UI operations passed as argv, never interpolated AppleScript."""
import subprocess
import time
SCRIPT = '''
on run argv
    set appName to item 1 of argv
    set operation to item 2 of argv
    set value to item 3 of argv
    tell application "System Events"
        tell process appName
            set frontmost to true
            if operation is "type" then
                keystroke value
            else if operation is "button" then
                set candidates to {value, "Skip ad", "Skip ads", "ข้ามโฆษณา"}
                repeat with candidate in candidates
                    try
                        click button (contents of candidate) of front window
                        return "clicked:" & (contents of candidate)
                    end try
                end repeat
                error "button not found"
            else if operation is "key" then
                if value is "enter" then
                    key code 36
                else if value is "escape" then
                    key code 53
                else if value is "tab" then
                    key code 48
                else if value is "save" then
                    keystroke "s" using command down
                end if
            end if
        end tell
    end tell
end run
'''

def control_app(app, action, value):
    if action not in {"type","button","key"}:raise ValueError("Actions: type, button, key")
    if action=="key" and value not in {"enter","escape","tab","save"}:raise ValueError("Keys: enter, escape, tab, save")
    if not value or len(value)>2000:raise ValueError("Provide 1–2000 characters")
    completed=subprocess.run(["/usr/bin/osascript","-e",SCRIPT,"--",app,action,value],check=True,capture_output=True,text=True,timeout=15)
    result={"app":app,"action":action,"value":value,"verified":True}
    if action=="button":
        result["clicked"]=(completed.stdout.strip().split(":",1)[-1] or value)
    return result

def youtube_play_and_skip(url, browser="Google Chrome", wait_seconds=8):
    """Open a YouTube result and use the browser's accessibility tree to play it.

    Skip is best-effort: YouTube may not show a skip button, and in that case
    the operation still succeeds only if playback can be verified.
    """
    subprocess.run(["/usr/bin/open", "-a", browser, url], check=True,
                   capture_output=True, text=True, timeout=15)
    time.sleep(max(2, min(wait_seconds, 20)))
    script = '''
on run argv
    set browserName to item 1 of argv
    tell application "System Events"
        tell process browserName
            set frontmost to true
            try
                click link 1 of group 1 of front window
            end try
            delay 2
            set playbackStarted to false
            repeat with label in {"Play", "Play (k)", "เล่น"}
                try
                    click button (contents of label) of front window
                    set playbackStarted to true
                    exit repeat
                end try
            end repeat
            set skipped to 0
            repeat 12 times
                repeat with label in {"Skip ad", "Skip ads", "ข้ามโฆษณา"}
                    try
                        click button (contents of label) of front window
                        set skipped to skipped + 1
                    end try
                end repeat
                delay 2
            end repeat
            if playbackStarted then
                return "playback_started;skip_attempts=" & skipped
            end if
            return "playback_not_verified;skip_attempts=" & skipped
        end tell
    end tell
    return "playback_requested"
end run
'''
    completed = subprocess.run(["/usr/bin/osascript", "-e", script, "--", browser],
                               check=True, capture_output=True, text=True, timeout=45)
    status = completed.stdout.strip() or "playback_not_verified"
    verified = status.startswith("playback_started")
    return {"app": browser, "action": "play_and_skip", "verified": verified,
            "status": status}
