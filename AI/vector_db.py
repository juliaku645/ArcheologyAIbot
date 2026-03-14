"""
Модуль для работы с векторной базой данных FAISS для хранения изображений.
"""
import os
import io
import hashlib
import numpy as np
import faiss
from datetime import datetime
from PIL import Image
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Optional


class VectorDatabase:
    """Класс для работы с векторной базой данных FAISS."""
    
    def __init__(self, 
                 faiss_index_path: str = "databases/faiss_index.bin",
                 faiss_metadata_path: str = "databases/faiss_metadata.npy",
                 clip_model_name: str = "clip-ViT-B-32",
                 embed_dim: int = 512):
        """
        Инициализация векторной базы данных.
        
        Args:
            faiss_index_path: Путь к файлу индекса FAISS
            faiss_metadata_path: Путь к файлу метаданных FAISS
            clip_model_name: Название модели CLIP для векторизации
            embed_dim: Размерность вектора эмбеддинга
        """
        self.faiss_index_path = faiss_index_path
        self.faiss_metadata_path = faiss_metadata_path
        self.embed_dim = embed_dim
        
        # Создаем директории, если их нет
        os.makedirs(os.path.dirname(faiss_index_path), exist_ok=True)
        
        # Загружаем модель CLIP
        self.clip_model = SentenceTransformer(clip_model_name)
        
        # Инициализируем FAISS индекс
        self._init_faiss()
    
    def _init_faiss(self):
        """Инициализация или загрузка FAISS индекса."""
        if os.path.exists(self.faiss_index_path):
            self.faiss_index = faiss.read_index(self.faiss_index_path)
            self.faiss_metadata = np.load(self.faiss_metadata_path, allow_pickle=True).tolist()
        else:
            self.faiss_index = faiss.IndexFlatL2(self.embed_dim)
            self.faiss_metadata = []
    
    def _save_faiss(self):
        """Сохранить FAISS индекс и метаданные."""
        faiss.write_index(self.faiss_index, self.faiss_index_path)
        np.save(self.faiss_metadata_path, self.faiss_metadata)
    
    def _hash(self, image_bytes: bytes) -> str:
        """
        Вычислить MD5 хеш изображения.
        
        Args:
            image_bytes: Байты изображения
            
        Returns:
            MD5 хеш в виде строки
        """
        return hashlib.md5(image_bytes).hexdigest()
    
    def _to_vector(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Преобразовать изображение в вектор с помощью CLIP.
        
        Args:
            image_bytes: Байты изображения
            
        Returns:
            Вектор эмбеддинга или None в случае ошибки
        """
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            vector = self.clip_model.encode(image, convert_to_numpy=True, normalize_embeddings=True)
            return vector.astype('float32')
        except Exception as e:
            print(f"Ошибка при векторизации изображения: {e}")
            return None
    
    def add_image(self, image_bytes: bytes) -> Tuple[str, int]:
        """
        Добавить изображение в векторную базу данных.
        
        Args:
            image_bytes: Байты изображения
            
        Returns:
            Кортеж (image_hash, faiss_index_id)
        """
        image_hash = self._hash(image_bytes)
        
        # Векторизация
        vector = self._to_vector(image_bytes)
        if vector is None:
            raise ValueError("Не удалось векторизовать изображение")
        
        # Добавление в FAISS
        self.faiss_index.add(vector.reshape(1, -1))
        faiss_id = len(self.faiss_metadata)
        self.faiss_metadata.append({
            "image_hash": image_hash,
            "added_at": datetime.now().isoformat()
        })
        
        # Сохранение
        self._save_faiss()
        
        return image_hash, faiss_id
    
    def search_similar(self, image_bytes: bytes, top_k: int = 3) -> List[str]:
        """
        Найти похожие изображения в векторной базе данных.
        
        Args:
            image_bytes: Байты изображения для поиска
            top_k: Количество похожих изображений для возврата
            
        Returns:
            Список хешей похожих изображений
        """
        vector = self._to_vector(image_bytes)
        if vector is None or self.faiss_index.ntotal == 0:
            return []
        
        # Поиск похожих векторов
        distances, indices = self.faiss_index.search(vector.reshape(1, -1), top_k)
        
        # Получаем хеши похожих изображений
        similar_hashes = []
        for idx in indices[0]:
            if 0 <= idx < len(self.faiss_metadata):
                hash_val = self.faiss_metadata[idx]["image_hash"]
                similar_hashes.append(hash_val)
        
        return similar_hashes
    
    def get_stats(self) -> dict:
        """
        Получить статистику векторной базы данных.
        
        Returns:
            Словарь со статистикой
        """
        return {
            "vectors": self.faiss_index.ntotal,
            "embed_dim": self.embed_dim
        }
