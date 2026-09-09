"""Explicit UI operations passed as argv, never interpolated AppleScript."""
import subprocess
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
                click button value of front window
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
    subprocess.run(["/usr/bin/osascript","-e",SCRIPT,"--",app,action,value],check=True,capture_output=True,text=True,timeout=15)
    return {"app":app,"action":action,"value":value}
