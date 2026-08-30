from app.core.assistant import Assistant

def main():
    assistant = Assistant()
    print("=" * 60)
    print("J.A.R.V.I.S. LOCAL")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 60)

    while True:
        try:
            user = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if user.lower() in {"exit", "quit"}:
            break
        if not user:
            continue

        assistant.chat(user)

if __name__ == "__main__":
    main()
