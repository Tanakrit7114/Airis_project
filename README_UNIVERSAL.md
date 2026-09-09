# Airis Universal AI

Operator session permissions now include public web search. File scope defaults to the current user's home directory; choose another existing directory, or / for all locations readable by the OS account. macOS-protected locations still require OS permission. Search scans filenames and stops at 15,000 entries / 12 matches; it is not a complete disk index.

Commands:

- list apps / รายชื่อแอป: discover .app bundles in /Applications, /System/Applications and ~/Applications.
- open app <name or .app path>: opens an installed app.
- read file <absolute path> / อ่านไฟล์ <path>: reads UTF-8 text, at most 1 MB with a 16,000-character preview.
- open file <absolute path> / เปิดไฟล์ <path>: opens a document using its associated app, requiring file and system permissions. Executable scripts and apps are excluded from this action.
- search web <query> / ค้นเว็บ <query> / ค้นอินเทอร์เน็ต <query>: public search snippets, original source links and retrieval timestamps. No claim that full pages were read. Search providers may rate-limit requests, and private/paywalled pages are not bypassed.
- control app {"app":"Notes","action":"type","value":"Hello"}: queue a specific UI action. Confirm with ยืนยัน / confirm within 60 seconds; ยกเลิก / cancel discards it. Supported actions: type, button (accessible button name in front window), key (enter, escape, tab, save). Requires macOS Accessibility/Automation permission granted manually. Custom UI elements and apps without accessible controls may not work.

This is not unrestricted root access or guaranteed control of every app/system. It does not automate transactions or bypass OS protections. Source URLs come from returned search metadata, not generated citations. Search query text is sent to public search providers only for the requested web search; local file contents are not attached to those requests.
