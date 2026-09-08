# telegram_client_module/telethon_client.py

import asyncio
import logging
from typing import Dict, Optional, Any, List
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import User # <-- Цей імпорт важливий для типізації
import asyncpg # Для роботи з пулом підключень до БД
from asyncpg.pool import Pool as DBPool # Для анотації типу

logger = logging.getLogger(__name__)

class TelethonClientManager:
    def __init__(self, api_id: int, api_hash: str):
        self.clients: Dict[str, TelegramClient] = {}
        self.db_pool: Optional[DBPool] = None
        self.api_id = api_id
        self.api_hash = api_hash
        logger.info(f"TelethonClientManager ініціалізовано з API_ID: {self.api_id}")

    async def initialize(self, db_pool: DBPool) -> None:
        """
        Ініціалізує менеджер, встановлюючи пул підключень до БД та завантажуючи існуючі сесії.
        """
        if self.db_pool is not None:
            logger.warning("TelethonClientManager вже ініціалізовано з пулом БД. Пропуск повторної ініціалізації.")
            return

        self.db_pool = db_pool
        logger.info("TelethonClientManager отримав пул підключень до БД.")

        await self._load_all_sessions_from_db() # Цей метод використовується під час ініціалізації для підключення клієнтів

    async def _execute_query(self, query: str, *args: Any, fetch: bool = False, fetchrow: bool = False, fetchval: bool = False) -> Any:
        """Допоміжна функція для виконання запитів до БД."""
        if not self.db_pool:
            logger.error("Пул підключень до бази даних не ініціалізовано в TelethonClientManager.")
            raise RuntimeError("Database pool is not initialized.")
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                if fetchval:
                    return await conn.fetchval(query, *args)
                elif fetchrow:
                    return await conn.fetchrow(query, *args)
                elif fetch:
                    return await conn.fetch(query, *args)
                else:
                    await conn.execute(query, *args)
        return None

    async def _load_all_sessions_from_db(self) -> None:
        """
        Завантажує всі збережені сесії з бази даних і підключає відповідних клієнтів.
        Викликається під час запуску.
        """
        logger.info("Завантаження всіх сесій Telethon з БД.")
        try:
            records = await self.get_all_sessions_from_db()
            for record in records:
                phone_number_from_db = record['phone_number'] # Зберігаємо початковий phone_number з БД
                session_string = record['session_string']
                
                client = TelegramClient(
                    StringSession(session_string),
                    self.api_id,
                    self.api_hash,
                    system_version="4.16.30-arm64-v8a",
                    device_model="Refridex Aiogram Bot",
                    app_version="Refridex Bot 1.0"
                )
                
                try:
                    await client.connect()
                    if await client.is_user_authorized():
                        # --- ВИПРАВЛЕНО: Видалено update_status=True ---
                        user_info = await client.get_me()
                        if user_info:
                            real_phone_number = user_info.phone or str(user_info.id)
                            # Якщо номер телефону змінився (наприклад, з placeholder на реальний)
                            if phone_number_from_db != real_phone_number:
                                logger.info(f"Оновлюємо phone_number в БД з '{phone_number_from_db}' на '{real_phone_number}'.")
                                # Видаляємо стару сесію і зберігаємо нову
                                await self.delete_session(phone_number_from_db)
                                await self.save_session_to_db(real_phone_number, client)
                                self.clients[real_phone_number] = client # Додаємо клієнта в кеш за новим ключем
                            else:
                                self.clients[phone_number_from_db] = client # Додаємо клієнта в кеш
                            
                            logger.info(f"Клієнт Telethon для {real_phone_number} (@{user_info.username or 'N/A'}) успішно завантажено та підключено.")
                        else:
                            logger.warning(f"Не вдалося отримати інформацію про користувача для клієнта {phone_number_from_db}. Сесія може бути недійсною.")
                            await self.delete_session(phone_number_from_db)
                            await client.disconnect()

                    else:
                        logger.warning(f"Клієнт Telethon для номера {phone_number_from_db} не авторизований, видалення сесії з БД.")
                        await self.delete_session(phone_number_from_db) # Видаляємо неавторизовану сесію
                        await client.disconnect() # Відключаємо
                except Exception as e:
                    logger.error(f"Помилка завантаження або підключення клієнта Telethon для {phone_number_from_db}: {e}", exc_info=True)
                    # Якщо виникає помилка, можливо, сесія пошкоджена, тому видаляємо її.
                    # Це було причиною попередньої втрати сесії, тому будьте обережні з цією логікою.
                    # Залишаємо її поки що, щоб побачити, чи виникне помилка після виправлення get_me().
                    await self.delete_session(phone_number_from_db)
                    if client.is_connected():
                        await client.disconnect()
            logger.info(f"Завантажено {len(self.clients)} активних Telethon клієнтів.")
        except Exception as e:
            logger.error(f"Помилка при завантаженні Telethon сесій з БД: {e}", exc_info=True)

    async def get_all_sessions_from_db(self) -> List[Dict[str, Any]]:
        """
        Отримує всі збережені сесії Telethon з бази даних.
        Повертає список словників з 'phone_number', 'session_string', 'api_id', 'api_hash', 'last_login'.
        """
        logger.debug("Отримання всіх сесій Telethon з БД для перевірки статусу.")
        try:
            records = await self._execute_query("SELECT phone_number, session_string, api_id, api_hash, last_login FROM telethon_sessions;", fetch=True)
            # Перетворюємо Record об'єкти на словники
            return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"Помилка отримання всіх Telethon сесій з БД: {e}", exc_info=True)
            return []

    async def save_session_to_db(self, phone_number: str, client: TelegramClient) -> None:
        """
        Зберігає сесію Telethon для даного клієнта в базу даних.
        """
        session_string = client.session.save()
        # Отримуємо api_id та api_hash з самого клієнта
        api_id = client.api_id
        api_hash = client.api_hash

        logger.info(f"Збереження сесії для {phone_number} в БД.")
        try:
            await self._execute_query(
                "INSERT INTO telethon_sessions (phone_number, session_string, api_id, api_hash, last_login) "
                "VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP) " # CURRENT_TIMESTAMP використовує час БД
                "ON CONFLICT (phone_number) DO UPDATE SET session_string = $2, api_id = $3, api_hash = $4, last_login = CURRENT_TIMESTAMP;",
                phone_number, session_string, api_id, api_hash
            )
            self.clients[phone_number] = client # Додаємо клієнта в кеш менеджера
            logger.info(f"Сесія для {phone_number} успішно збережена.")
        except Exception as e:
            logger.error(f"Помилка збереження сесії для {phone_number} в БД: {e}", exc_info=True)

    async def load_session_from_db(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Завантажує дані сесії Telethon для даного номера телефону з бази даних.
        Повертає словник з даними сесії або None, якщо не знайдено.
        """
        logger.debug(f"Завантаження сесії для {phone_number} з БД.")
        try:
            record = await self._execute_query(
                "SELECT session_string, api_id, api_hash FROM telethon_sessions WHERE phone_number = $1;",
                phone_number, fetchrow=True
            )
            if record:
                return dict(record)
            return None
        except Exception as e:
            logger.error(f"Помилка завантаження сесії для {phone_number} з БД: {e}", exc_info=True)
            return None

    async def delete_session(self, phone_number: str) -> None:
        """
        Видаляє сесію Telethon для даного номера телефону з бази даних.
        """
        logger.info(f"Видалення сесії для {phone_number} з БД.")
        try:
            await self._execute_query(
                "DELETE FROM telethon_sessions WHERE phone_number = $1;",
                phone_number
            )
            # Також видаляємо з кешу менеджера, якщо вона там є
            self.clients.pop(phone_number, None)
            logger.info(f"Сесія для {phone_number} успішно видалена з БД.")
        except Exception as e:
            logger.error(f"Помилка видалення сесії для {phone_number} з БД: {e}", exc_info=True)

    def add_client(self, phone_number: str, client: TelegramClient) -> None:
        """Додає клієнта до менеджера."""
        self.clients[phone_number] = client
        logger.info(f"Клієнт для {phone_number} додано до кешу менеджера.")

    def get_client(self, phone_number: str) -> Optional[TelegramClient]:
        """Повертає клієнта за номером телефону."""
        return self.clients.get(phone_number)

    def get_all_active_clients(self) -> Dict[str, TelegramClient]:
        """Повертає словник усіх активних клієнтів (номер телефону: клієнт)."""
        return self.clients

    async def get_any_active_client(self) -> Optional[TelegramClient]:
        """Повертає першого підключеного та авторизованого клієнта."""
        for client in self.clients.values():
            if client.is_connected() and await client.is_user_authorized():
                return client
        return None

    async def _get_client_detailed_info(self, client: TelegramClient, phone_key: str) -> Dict[str, Any]:
        """
        Отримує детальну інформацію про клієнта, включаючи дані користувача з Telegram.
        """
        info = {
            "id": "N/A",
            "first_name": "N/A",
            "last_name": "N/A",
            "username": "@Відсутній",
            "phone": phone_key, # Використовуємо ключ з clients, як замовчування
            "status": "Не підключено"
        }
        
        if client.is_connected():
            info["status"] = "Підключено"
            try:
                # --- ВИПРАВЛЕНО: Видалено update_status=True ---
                user_info = await client.get_me()
                if user_info:
                    info["id"] = user_info.id
                    info["first_name"] = user_info.first_name or "N/A"
                    info["last_name"] = user_info.last_name or "N/A"
                    info["username"] = f"@{user_info.username}" if user_info.username else "@Відсутній"
                    info["phone"] = user_info.phone or phone_key # Перевага реальному телефону з get_me()
                else:
                    logger.warning(f"Не вдалося отримати user_info для клієнта з ключем: {phone_key}")
            except Exception as e:
                logger.warning(f"Помилка при отриманні інформації про користувача для клієнта {phone_key}: {e}", exc_info=True)
                info["status"] = "Підключено (помилка отримання інфо)"
        return info

    async def get_all_client_statuses(self) -> List[Dict[str, Any]]:
        """
        Повертає список детальних статусів для всіх керованих клієнтів.
        """
        statuses = []
        for phone_key, client in self.clients.items():
            detailed_info = await self._get_client_detailed_info(client, phone_key)
            statuses.append({
                "authorized": await client.is_user_authorized(), # Перевіряємо статус авторизації
                "info": detailed_info
            })
        if not statuses:
            logger.info("Немає активних Telethon клієнтів для відображення статусу.")
        return statuses

    async def shutdown_all_clients(self) -> None:
        """Відключає всі активні Telethon клієнти."""
        logger.info("Початок відключення всіх Telethon клієнтів.")
        for phone_number, client in list(self.clients.items()): # Ітеруємо по копії, щоб можна було видаляти
            if client.is_connected():
                try:
                    await client.disconnect()
                    logger.info(f"Telethon клієнт для {phone_number} відключено.")
                except Exception as e:
                    logger.error(f"Помилка відключення клієнта {phone_number}: {e}", exc_info=True)
            self.clients.pop(phone_number, None) # Видаляємо з кешу
        logger.info("Усі Telethon клієнти відключено.")