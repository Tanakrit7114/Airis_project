class EmbeddingModel:

    def embed(self, text: str):
        raise NotImplementedError

    def embed_many(self, texts):
        return [
            self.embed(text)
            for text in texts
        ]
