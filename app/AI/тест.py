import asyncio
import aiosqlite
import hashlib
import base64
import os
import io
import numpy as np
import faiss
from datetime import datetime
from PIL import Image
from sentence_transformers import SentenceTransformer
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


# ==================== КОНФИГУРАЦИЯ ====================
class Config:
    def __init__(self):
        self.faiss_index_path = "vector_storage/faiss_index.bin"
        self.faiss_metadata_path = "vector_storage/faiss_metadata.npy"
        self.sqlite_db_path = "database/images_metadata.db"
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.clip_model_name = "clip-ViT-B-32"
        self.embed_dim = 512

        os.makedirs("vector_storage", exist_ok=True)
        os.makedirs("database", exist_ok=True)


# ==================== RAG СИСТЕМА ====================
class RAGImageSystem:
    """RAG система для работы с изображениями - ничего не делает при импорте"""

    def __init__(self, config):
        self.config = config
        self.clip_model = SentenceTransformer(config.clip_model_name)

        if config.openai_api_key:
            self.llm = ChatOpenAI(
                model="gpt-4-vision-preview",
                api_key=config.openai_api_key,
                max_tokens=300
            )
        else:
            self.llm = None

        self._init_faiss()

    # ========== FAISS ==========
    def _init_faiss(self):
        if os.path.exists(self.config.faiss_index_path):
            self.faiss_index = faiss.read_index(self.config.faiss_index_path)
            self.faiss_metadata = np.load(self.config.faiss_metadata_path, allow_pickle=True).tolist()
        else:
            self.faiss_index = faiss.IndexFlatL2(self.config.embed_dim)
            self.faiss_metadata = []

    async def _save_faiss(self):
        faiss.write_index(self.faiss_index, self.config.faiss_index_path)
        np.save(self.config.faiss_metadata_path, self.faiss_metadata)

    # ========== SQLite ==========
    async def _init_db(self):
        async with aiosqlite.connect(self.config.sqlite_db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    image_hash TEXT PRIMARY KEY,
                    description TEXT,
                    faiss_index_id INTEGER
                )
            """)
            await db.commit()

    # ========== Утилиты ==========
    def _hash(self, image_bytes: bytes) -> str:
        return hashlib.md5(image_bytes).hexdigest()

    def _to_vector(self, image_bytes: bytes) -> np.ndarray:
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        vector = self.clip_model.encode(image, convert_to_numpy=True, normalize_embeddings=True)
        return vector.astype('float32')

    # ========== Основные методы ==========
    async def add(self, image_bytes: bytes, description: str = ""):
        """Добавить изображение в базу"""
        await self._init_db()

        image_hash = self._hash(image_bytes)

        # Проверяем существование
        async with aiosqlite.connect(self.config.sqlite_db_path) as db:
            cursor = await db.execute("SELECT 1 FROM images WHERE image_hash = ?", (image_hash,))
            if await cursor.fetchone():
                return {"status": "exists", "hash": image_hash}

        # Векторизация
        vector = self._to_vector(image_bytes)
        if vector is None:
            return None

        # FAISS
        self.faiss_index.add(vector.reshape(1, -1))
        faiss_id = len(self.faiss_metadata)
        self.faiss_metadata.append({
            "image_hash": image_hash,
            "added_at": datetime.now().isoformat()
        })
        await self._save_faiss()

        # SQLite
        async with aiosqlite.connect(self.config.sqlite_db_path) as db:
            await db.execute(
                "INSERT INTO images (image_hash, description, faiss_index_id) VALUES (?, ?, ?)",
                (image_hash, description, faiss_id)
            )
            await db.commit()

        return {"status": "added", "hash": image_hash, "faiss_id": faiss_id}

    async def search(self, image_bytes: bytes, top_k: int = 3):
        """Найти похожие изображения, вернуть их описания"""
        await self._init_db()

        vector = self._to_vector(image_bytes)
        if vector is None or self.faiss_index.ntotal == 0:
            return []

        distances, indices = self.faiss_index.search(vector.reshape(1, -1), top_k)

        descriptions = []
        async with aiosqlite.connect(self.config.sqlite_db_path) as db:
            for idx in indices[0]:
                if idx < 0 or idx >= len(self.faiss_metadata):
                    continue
                hash_val = self.faiss_metadata[idx]["image_hash"]
                cursor = await db.execute("SELECT description FROM images WHERE image_hash = ?", (hash_val,))
                row = await cursor.fetchone()
                if row and row[0]:
                    descriptions.append(row[0])

        return descriptions

    async def ask(self, image_bytes: bytes, user_context: str = ""):
        """Спросить LLM с учетом похожих изображений"""
        if not self.llm:
            return "LLM не доступна (нет API ключа)"

        await self._init_db()

        # Поиск контекста
        similar = await self.search(image_bytes, top_k=3)
        context = "\n".join([f"- {d}" for d in similar]) if similar else ""

        # Запрос к LLM
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        messages = [
            SystemMessage(content=("SYSTEM_PROMPT")),
            HumanMessage(content=[
                {"type": "text",
                 "text": f"Контекст пользователя: {user_context}\n\nПохожие описания из базы:\n{context}\n\nОпиши это изображение."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ])
        ]


        response = await self.llm.ainvoke(messages)
        return response.content

    async def stats(self):
        """Статистика базы"""
        await self._init_db()
        async with aiosqlite.connect(self.config.sqlite_db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM images")
            count = (await cursor.fetchone())[0]

        return {
            "images": count,
            "vectors": self.faiss_index.ntotal
        }