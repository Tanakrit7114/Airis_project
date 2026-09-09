from datetime import datetime


def get_system_info():
    now = datetime.now()

    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": now.strftime("%A"),
    }


def system_tool(query: str):
    """
    Return current system date/time information.
    """

    query_lower = query.lower()

    info = get_system_info()

    # Date
    if (
        "date" in query_lower
        or "today" in query_lower
        or "วันที่" in query_lower
        or "วันอะไร" in query_lower
    ):
        return (
            f"Today is {info['weekday']}, "
            f"{info['date']}."
        )

    # Time
    if (
        "time" in query_lower
        or "กี่โมง" in query_lower
        or "เวลา" in query_lower
    ):
        return (
            f"The current time is "
            f"{info['time']}."
        )

    # Default
    return (
        f"Current date and time: "
        f"{info['datetime']}"
    )
