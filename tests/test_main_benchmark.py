from app import main


class FakeAssistant:
    def __init__(self):
        self.called = False

    def benchmark(self):
        self.called = True
        return {
            "tokens": 32,
            "total_time": 1.0,
            "ttft": 0.2,
            "tokens_per_sec": 32.0,
        }


def test_benchmark_mode(monkeypatch, capsys):
    fake = FakeAssistant()

    monkeypatch.setattr(
        main,
        "Assistant",
        lambda: fake,
    )

    monkeypatch.setattr(
        main.sys,
        "argv",
        ["app.main", "--benchmark"],
    )

    main.main()

    output = capsys.readouterr().out

    assert fake.called
    assert "BENCHMARK" in output
    assert "Tokens: 32" in output
    assert "Tokens/sec: 32.00" in output
