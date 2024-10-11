from .base import Memory, create_embedding
import numpy as np
import faiss
import io
import sqlite3


class STMTs:
    TABLE = """
    CREATE TABLE IF NOT EXISTS memory (
        text TEXT,
        embedding NDARRAY
    )
    """

    INSERT = """
    INSERT INTO memory VALUES((:text), (:embedding))
    """

    RESET = """
    DELETE FROM memory
    """

    FETCH = """
    SELECT ROWID, text FROM memory WHERE ROWID=:rowid
    """

    COUNT = """
    SELECT count(*) FROM memory
    """


# https://stackoverflow.com/questions/18621513/python-insert-numpy-array-into-sqlite3-database
def adapt_array(ar: np.ndarray):
    buf = io.BytesIO()
    np.save(buf, ar)
    buf.seek(0)
    return sqlite3.Binary(buf.read())


def convert_array(blob):
    buf = io.BytesIO(blob)
    buf.seek(0)
    return np.load(buf)


sqlite3.register_adapter(np.ndarray, adapt_array)
sqlite3.register_converter("NDARRAY", convert_array)


# via AutoGPT
class LocalMemory(Memory):
    N_DIM = 1536

    def __init__(self, path=None):
        if not path:
            # os.makedirs('memories', exist_ok=True)
            # path = datetime.datetime.now().strftime('memories/%Y%m%d-%H%M%s.db')
            path = ":memory:"
        self._conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        self._cur = self._conn.cursor()
        self._cur.execute(STMTs.TABLE)
        self._faiss = faiss.IndexFlatL2(self.N_DIM)

    def add(self, text: str):
        embedding = create_embedding(text)
        self._cur.execute(STMTs.INSERT, dict(text=text, embedding=embedding))
        self._conn.commit()
        self._faiss.add(embedding.reshape(1, -1))

    def clear(self):
        self._faiss.reset()
        self._cur.execute(STMTs.RESET)
        self._conn.commit()

    def get(self, text: str):
        return self.get_relevant(text, 1)

    def get_relevant(self, text, k=5):
        embedding = create_embedding(text)
        D, I = self._faiss.search(embedding.reshape(1, -1), k=k)

        texts = []
        for i in I[0]:
            i = int(i)
            if i == -1:
                continue
            rowid, text = self._cur.execute(STMTs.FETCH, dict(rowid=i+1)).fetchone()
            texts.append(text)
        return texts

    def get_stats(self):
        sqlite_count = self._cur.execute(STMTs.COUNT).fetchone()[0]
        faiss_count = self._faiss.ntotal
        return f'<Stats n_dim={self.N_DIM} sqlite={sqlite_count} faiss={faiss_count}>'


if __name__ == '__main__':
    import openai_monkey.hardware
    memory = LocalMemory()
    memory.add('hello')
    print(memory.get_stats())
    memory.add('world')
    print(memory.get_stats())

    _ = memory.get_relevant('hi')
    print('relevant', _)
    memory.clear()
    print(memory.get_stats())
