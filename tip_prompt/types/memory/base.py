import openai
import abc
import numpy as np


def create_embedding(text) -> np.ndarray:
    embedding = openai.Embedding.create(
        input=[text],
        model="text-embedding-ada-002"
    )["data"][0]["embedding"]
    return np.array(embedding, dtype=np.float32)


class Memory(abc.ABC):
    @abc.abstractmethod
    def add(self, data):
        return NotImplemented

    @abc.abstractmethod
    def get(self, data):
        return NotImplemented

    @abc.abstractmethod
    def clear(self):
        return NotImplemented

    @abc.abstractmethod
    def get_relevant(self, data, k=5):
        return NotImplemented

    @abc.abstractmethod
    def get_stats(self):
        return NotImplemented
