from app.llm import LLMConfig, LLMEngine


class FakeResponse:
    def __init__(self, text, generation_tokens=None, finish_reason=None):
        self.text = text
        if generation_tokens is not None:
            self.generation_tokens = generation_tokens
        if finish_reason is not None:
            self.finish_reason = finish_reason


class FakeTokenizer:
    def encode(self, text):
        return text.split()


def test_should_continue_on_length_limit():
    config = LLMConfig(max_continuations=2, continuation_min_ratio=0.92)
    engine = LLMEngine.__new__(LLMEngine)
    engine.config = config
    engine._shutdown_requested = False

    assert engine._should_continue(
        "1. First section\n2. Second section continues:",
        generated_tokens=100,
        generation_tokens=100,
        finish_reason="length",
    ) is True


def test_should_not_continue_on_normal_stop():
    config = LLMConfig(max_continuations=2, continuation_min_ratio=0.92)
    engine = LLMEngine.__new__(LLMEngine)
    engine.config = config
    engine._shutdown_requested = False

    assert engine._should_continue(
        "This answer is complete.",
        generated_tokens=100,
        generation_tokens=100,
        finish_reason="stop",
    ) is False


def test_continuation_messages_do_not_duplicate_answer_turns():
    engine = LLMEngine.__new__(LLMEngine)
    base = [{"role": "system", "content": "system"}, {"role": "user", "content": "question"}]
    messages = engine._build_continuation_messages(base, "partial answer")

    assert messages[-2] == {"role": "assistant", "content": "partial answer"}
    assert messages[-1]["role"] == "user"
    assert len(messages) == 4


def test_should_continue_on_normal_stop_when_answer_is_clearly_incomplete():
    config = LLMConfig(max_continuations=2, continuation_min_ratio=0.92)
    engine = LLMEngine.__new__(LLMEngine)
    engine.config = config
    engine._shutdown_requested = False

    assert engine._should_continue(
        "1. การคำนวณแบบ Threshold:",
        generated_tokens=100,
        generation_tokens=100,
        finish_reason="stop",
    ) is True
