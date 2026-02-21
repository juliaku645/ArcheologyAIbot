"""
Модуль для парсинга данных с сайта goskatalog.ru.
"""
import requests
import os
import hashlib
import logging
import time
from typing import Optional, List, Dict
from .database import ImageDatabase
from .vector_db import VectorDatabase

# Настройка логирования (только если еще не настроено)
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

logger = logging.getLogger(__name__)


class GoskatalogParser:
    """Класс для парсинга данных с сайта goskatalog.ru."""
    
    def __init__(self, 
                 db: ImageDatabase,
                 vector_db: VectorDatabase,
                 db_path: str = "AI/goskatalog.db"):
        """
        Инициализация парсера.
        
        Args:
            db: Экземпляр ImageDatabase для хранения описаний
            vector_db: Экземпляр VectorDatabase для хранения изображений
            db_path: Путь к локальной базе данных парсера
        """
        self.db = db
        self.vector_db = vector_db
        
        # URL для API goskatalog
        self.EXHIBIT_URL = "https://goskatalog.ru/muzfo-rest/rest/exhibits/{}"
        self.IMAGE_URL = "https://goskatalog.ru/muzfo-imaginator/rest/images/public/150/{}/{}.jpg"
        
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        self.db_path = db_path
        self.collected = 0
        self.skipped_existing = 0
        self.failed_images = 0
        self.failed_exhibits = 0
    
    def _get_image_hash(self, image_bytes: bytes) -> str:
        """
        Вычислить MD5 хеш изображения.
        
        Args:
            image_bytes: Байты изображения
            
        Returns:
            MD5 хеш в виде строки
        """
        return hashlib.md5(image_bytes).hexdigest()
    
    async def process_exhibit(self, object_id: int) -> bool:
        """
        Обработать один экспонат с сайта goskatalog.
        
        Args:
            object_id: ID экспоната на сайте
            
        Returns:
            True, если обработка прошла успешно, иначе False
        """
        start_time = time.time()
        logger.info(f"Начало обработки экспоната ID: {object_id}")
        
        try:
            # Получаем описание экспоната
            logger.debug(f"Запрос данных экспоната {object_id}...")
            request_start = time.time()
            resp = requests.get(self.EXHIBIT_URL.format(object_id), headers=self.HEADERS, timeout=10)
            request_time = time.time() - request_start
            
            if resp.status_code != 200:
                logger.warning(f"Экспонат {object_id}: HTTP статус {resp.status_code} (время запроса: {request_time:.2f}с)")
                self.failed_exhibits += 1
                return False
            
            logger.debug(f"Экспонат {object_id}: данные получены за {request_time:.2f}с")
            
            # Парсим JSON
            try:
                data = resp.json()
            except Exception as e:
                logger.error(f"Экспонат {object_id}: ошибка парсинга JSON - {e}")
                self.failed_exhibits += 1
                return False
            
            description = data.get("description", "").strip()
            description_length = len(description)
            
            if not description:
                logger.warning(f"Экспонат {object_id}: описание отсутствует или пустое")
                self.failed_exhibits += 1
                return False
            
            logger.info(f"Экспонат {object_id}: описание получено ({description_length} символов)")
            
            # Получаем изображения
            images = data.get("images", [])
            images_count = len(images)
            
            if not images:
                logger.warning(f"Экспонат {object_id}: изображения отсутствуют")
                self.failed_exhibits += 1
                return False
            
            logger.info(f"Экспонат {object_id}: найдено {images_count} изображений")
            
            # Статистика обработки изображений
            processed_count = 0
            skipped_count = 0
            failed_count = 0
            
            # Обрабатываем каждое изображение
            for idx, img in enumerate(images, 1):
                image_id = img.get("id")
                if not image_id:
                    logger.warning(f"Экспонат {object_id}, изображение #{idx}: ID отсутствует")
                    failed_count += 1
                    continue
                
                logger.debug(f"Экспонат {object_id}, изображение #{idx}/{images_count} (ID: {image_id}): начало обработки")
                image_start_time = time.time()
                
                try:
                    # Скачиваем изображение
                    img_url = self.IMAGE_URL.format(image_id, image_id)
                    logger.debug(f"Экспонат {object_id}, изображение {image_id}: загрузка с {img_url}")
                    
                    download_start = time.time()
                    img_resp = requests.get(img_url, timeout=10)
                    download_time = time.time() - download_start
                    
                    if img_resp.status_code != 200:
                        logger.warning(f"Экспонат {object_id}, изображение {image_id}: HTTP статус {img_resp.status_code} (время загрузки: {download_time:.2f}с)")
                        failed_count += 1
                        continue
                    
                    image_bytes = img_resp.content
                    image_size = len(image_bytes)
                    image_size_kb = image_size / 1024
                    
                    logger.debug(f"Экспонат {object_id}, изображение {image_id}: загружено {image_size_kb:.2f} KB за {download_time:.2f}с")
                    
                    # Вычисляем хеш
                    hash_start = time.time()
                    image_hash = self._get_image_hash(image_bytes)
                    hash_time = time.time() - hash_start
                    logger.debug(f"Экспонат {object_id}, изображение {image_id}: хеш вычислен за {hash_time:.3f}с ({image_hash[:8]}...)")
                    
                    # Проверяем, не существует ли уже это изображение
                    check_start = time.time()
                    exists = await self.db.image_exists(image_hash)
                    check_time = time.time() - check_start
                    
                    if exists:
                        logger.info(f"Экспонат {object_id}, изображение {image_id}: уже существует в БД (пропущено, проверка заняла {check_time:.3f}с)")
                        skipped_count += 1
                        self.skipped_existing += 1
                        continue
                    
                    # Добавляем в векторную БД
                    logger.debug(f"Экспонат {object_id}, изображение {image_id}: добавление в векторную БД...")
                    vector_start = time.time()
                    try:
                        _, faiss_index_id = self.vector_db.add_image(image_bytes)
                        vector_time = time.time() - vector_start
                        logger.debug(f"Экспонат {object_id}, изображение {image_id}: добавлено в FAISS (ID: {faiss_index_id}, время: {vector_time:.2f}с)")
                    except Exception as e:
                        logger.error(f"Экспонат {object_id}, изображение {image_id}: ошибка при добавлении в векторную БД - {e}", exc_info=True)
                        failed_count += 1
                        self.failed_images += 1
                        continue
                    
                    # Добавляем описание в SQLite
                    logger.debug(f"Экспонат {object_id}, изображение {image_id}: добавление описания в SQLite...")
                    db_start = time.time()
                    await self.db.add_image(image_hash, description, faiss_index_id)
                    db_time = time.time() - db_start
                    logger.debug(f"Экспонат {object_id}, изображение {image_id}: описание добавлено в SQLite за {db_time:.3f}с")
                    
                    self.collected += 1
                    processed_count += 1
                    image_total_time = time.time() - image_start_time
                    
                    logger.info(
                        f"✅ Экспонат {object_id}, изображение {image_id}: успешно добавлено "
                        f"(#{self.collected}, размер: {image_size_kb:.2f} KB, "
                        f"хеш: {image_hash[:8]}..., время обработки: {image_total_time:.2f}с)"
                    )
                    
                except Exception as e:
                    failed_count += 1
                    self.failed_images += 1
                    image_total_time = time.time() - image_start_time
                    logger.error(
                        f"❌ Экспонат {object_id}, изображение {image_id}: ошибка при обработке - {e} "
                        f"(время до ошибки: {image_total_time:.2f}с)",
                        exc_info=True
                    )
                    continue
            
            # Итоговая статистика по экспонату
            total_time = time.time() - start_time
            logger.info(
                f"Экспонат {object_id}: обработка завершена за {total_time:.2f}с. "
                f"Статистика: обработано {processed_count}, пропущено {skipped_count}, ошибок {failed_count} из {images_count}"
            )
            
            return processed_count > 0 or skipped_count > 0
            
        except requests.exceptions.Timeout:
            logger.error(f"Экспонат {object_id}: таймаут при запросе данных")
            self.failed_exhibits += 1
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Экспонат {object_id}: ошибка сетевого запроса - {e}")
            self.failed_exhibits += 1
            return False
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(
                f"❌ Экспонат {object_id}: критическая ошибка при обработке - {e} "
                f"(время до ошибки: {total_time:.2f}с)",
                exc_info=True
            )
            self.failed_exhibits += 1
            return False
    
    async def run(self, start_id: int = 68220511, max_images: int = 100, max_attempts: int = 500):
        """
        Запустить парсинг данных с сайта goskatalog.
        
        Args:
            start_id: Начальный ID экспоната для парсинга
            max_images: Максимальное количество изображений для сбора
            max_attempts: Максимальное количество попыток
        """
        print(f"🚀 Начало парсинга goskatalog.ru (максимум {max_images} изображений)")
        
        current_id = start_id
        attempts = 0
        
        while self.collected < max_images and attempts < max_attempts:
            print(f"\n🔍 Обработка экспоната ID: {current_id}")
            await self.process_exhibit(current_id)
            
            current_id += 1
            attempts += 1
            
            if self.collected >= max_images:
                break
        
        logger.info(
            f"\n✅ Парсинг завершен! "
            f"Собрано: {self.collected} изображений, "
            f"пропущено (уже есть): {self.skipped_existing}, "
            f"ошибок изображений: {self.failed_images}, "
            f"ошибок экспонатов: {self.failed_exhibits}"
        )
