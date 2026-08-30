import sys

from app.core.assistant import Assistant


def run_benchmark(assistant):
    result = assistant.benchmark()

    print("\n[BENCHMARK]")
    print(f"Tokens: {result['tokens']}")
    print(f"Total time: {result['total_time']:.3f}s")
    print(f"TTFT: {result['ttft']:.3f}s")
    print(f"Tokens/sec: {result['tokens_per_sec']:.2f}")


def main():

    assistant = Assistant()

    if "--benchmark" in sys.argv:
        try:
            run_benchmark(assistant)
        finally:
            shutdown = getattr(assistant, "shutdown", None)
            if callable(shutdown):
                shutdown()
        return

    print("=" * 60)
    print("J.A.R.V.I.S. LOCAL")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 60)

    try:
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

    finally:
        assistant.shutdown()


if __name__ == "__main__":
    main()