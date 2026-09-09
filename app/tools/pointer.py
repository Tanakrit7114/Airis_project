"""Direct, user-driven pointer events. No autonomous target selection."""
import math

def pointer_event(action,x,y):
    if action not in {"move","click"} or not all(math.isfinite(v) and 0<=v<=1 for v in (x,y)):
        raise ValueError("Pointer expects move/click and normalized coordinates in [0,1]")
    import Quartz as q
    if not q.AXIsProcessTrusted():
        raise PermissionError("อนุญาต Accessibility ให้โปรเซสที่รัน Airis ใน System Settings ก่อน")
    bounds=q.CGDisplayBounds(q.CGMainDisplayID())
    # Keep a margin from menu/hot-corner targets. Primary display coordinates.
    point=(bounds.origin.x+max(8,min(bounds.size.width-8,x*bounds.size.width)),
           bounds.origin.y+max(8,min(bounds.size.height-8,y*bounds.size.height)))
    event=q.CGEventCreateMouseEvent(None,q.kCGEventMouseMoved,point,q.kCGMouseButtonLeft)
    q.CGEventPost(q.kCGHIDEventTap,event)
    if action=="click":
        for kind in (q.kCGEventLeftMouseDown,q.kCGEventLeftMouseUp):
            q.CGEventPost(q.kCGHIDEventTap,q.CGEventCreateMouseEvent(None,kind,point,q.kCGMouseButtonLeft))
    return {"action":action,"x":point[0],"y":point[1],"source":"Quartz / primary display"}
