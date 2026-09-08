# database/db_search_functions.py
"""
Функції для взаємодії з базою даних, що стосуються каталогу та пошуку.
"""

import logging
import os
from typing import List, Dict, Optional
import aiofiles
import asyncpg

logger = logging.getLogger(__name__)


async def get_all_brands_with_count(db_pool: asyncpg.Pool) -> List[Dict]:
    """
    Виконує запит до БД для отримання списку брендів, які мають моделі,
    разом з кількістю моделей для кожного бренду.
    """
    try:
        file_path = os.path.join('database', 'sql_queries', 'get_brands_with_model_count.sql')
        
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
            sql_query = await file.read()

        async with db_pool.acquire() as connection:
            results = await connection.fetch(sql_query)
            return [dict(row) for row in results]
    except FileNotFoundError:
        logger.error(f"Файл SQL-запиту '{file_path}' не знайдено.")
        return []
    except Exception as e:
        logger.error(f"Помилка при виконанні запиту на отримання брендів: {e}", exc_info=True)
        return []


async def get_models_by_brand(db_pool: asyncpg.Pool, brand_name: str) -> List[Dict]:
    """
    Отримує список моделей для конкретного бренду.
    """
    try:
        file_path = os.path.join('database', 'sql_queries', 'get_models_by_brand.sql')
        
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
            sql_query = await file.read()

        async with db_pool.acquire() as connection:
            results = await connection.fetch(sql_query, brand_name)
            return [dict(row) for row in results]
    except FileNotFoundError:
        logger.error(f"Файл SQL-запиту '{file_path}' не знайдено.")
        return []
    except Exception as e:
        logger.error(f"Помилка при отриманні моделей для бренду '{brand_name}': {e}", exc_info=True)
        return []


async def get_model_details_by_id(db_pool: asyncpg.Pool, model_id: int) -> Optional[Dict]:
    """
    Отримує повну інформацію про конкретну модель за її ID.
    """
    try:
        file_path = os.path.join('database', 'sql_queries', 'get_model_details_by_id.sql')

        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
            sql_query = await file.read()

        async with db_pool.acquire() as connection:
            result = await connection.fetchrow(sql_query, model_id)
            if result:
                return dict(result)
            return None
    except FileNotFoundError:
        logger.error(f"Файл SQL-запиту '{file_path}' не знайдено.")
        return None
    except Exception as e:
        logger.error(f"Помилка при отриманні деталей моделі з ID {model_id}: {e}", exc_info=True)
        return None


async def find_in_database(db_pool: asyncpg.Pool, query: str) -> List[Dict]:
    """
    Виконує швидкий пошук моделей або брендів за ключовим словом.
    """
    clean_query = f"%{query.strip()}%"
    try:
        async with db_pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT 
                    b.brand_name AS brand,
                    cm.model_id,
                    CONCAT_WS(' ', b.brand_name, s.series_name_ukr) AS name
                FROM product_metadata.brands b
                JOIN product_metadata.brand_series s ON b.brand_id = s.brand_id
                JOIN conditioners.conditioner_models cm ON s.series_id = cm.series_id
                WHERE b.brand_name ILIKE $1 OR s.series_name_ukr ILIKE $1
                LIMIT 10;
            """, clean_query)
            return [dict(r) for r in results]
    except Exception as e:
        logger.warning(f"Пошук у БД не дав результату або таблиці відсутні: {e}")
        return []


def format_search_results(results: List[Dict]) -> str:
    """
    Форматує результати пошуку для виведення в чат.
    """
    if not results:
        return ""
    lines = []
    for idx, item in enumerate(results, 1):
        name = item.get('name') or item.get('brand', 'Модель')
        model_id = item.get('model_id')
        if model_id:
            lines.append(f"{idx}. ❄️ <b>{name}</b> (ID: <code>{model_id}</code>)")
        else:
            lines.append(f"{idx}. ❄️ <b>{name}</b>")
    return "\n".join(lines)