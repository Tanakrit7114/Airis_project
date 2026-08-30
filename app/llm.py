from mlx_lm import load, stream_generate
from app.config import MODEL


class LocalLLM:
    def __init__(self):
        self.model = None
        self.tokenizer = None

    def load(self):
        if self.model is not None:
            return

        print("\n[LLM] Loading model...")

        self.model, self.tokenizer = load(MODEL)

        print("[LLM] Model ready.\n")

    def _build_prompt(self, messages):
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    def stream(
        self,
        messages,
        max_tokens=512,
    ):
        self.load()

        prompt = self._build_prompt(messages)

        thinking = False
        answer_parts = []

        for response in stream_generate(
            self.model,
            self.tokenizer,
            prompt,
            max_tokens=max_tokens,
        ):
            text = response.text

            if not text:
                continue

            # Hide Qwen thinking output
            if "<think>" in text:
                thinking = True
                text = text.split("<think>", 1)[1]

            if thinking:
                if "</think>" in text:
                    thinking = False
                    text = text.split("</think>", 1)[1]
                else:
                    continue

            if not text:
                continue

            answer_parts.append(text)
            print(text, end="", flush=True)

        return "".join(answer_parts).strip()
