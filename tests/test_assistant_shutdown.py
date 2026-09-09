from app.assistant import Assistant


def test_assistant_shutdown():
    assistant = Assistant()

    assistant.llm.model_manager.model = object()
    assistant.llm.model_manager.tokenizer = object()

    assistant.shutdown()

    assert assistant.llm.model_manager.model is None
    assert assistant.llm.model_manager.tokenizer is None
