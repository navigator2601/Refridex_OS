# telegram_client_module/auth_telethon.py

import logging
import asyncio
import sys
import os
import inspect

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeExpiredError, PhoneCodeEmptyError, PhoneCodeInvalidError, FloodWaitError, RPCError
from config import config

from database.telethon_sessions_db import save_telethon_session, get_telethon_session, delete_telethon_session
from database.db_pool_manager import get_db_pool, create_db_pool, close_db_pool, init_db_tables

logger = logging.getLogger(__name__)

class CustomDBSessionString(StringSession):
    def __init__(self, session_id=None, db_pool_instance=None, api_id=None, api_hash=None):
        logger.debug(f"Initializing CustomDBSessionString for session_id: {session_id}")
        super().__init__()
        self.session_id = session_id
        self.db_pool = db_pool_instance
        self.api_id = api_id
        self.api_hash = api_hash
        self._loop = None

    async def load(self):
        logger.debug(f"Loading session '{self.session_id}' from DB.")
        if not self.db_pool:
            logger.warning("DB pool not set for CustomDBSessionString. Cannot load session.")
            return

        session_string_bytes = await get_telethon_session(self.db_pool, self.session_id)
        if session_string_bytes:
            try:
                self.set_string(session_string_bytes.decode('utf-8'))
                logger.info(f"Сесія '{self.session_id}' успішно завантажена з БД.")
            except Exception as e:
                logger.error(f"Помилка при завантаженні сесії '{self.session_id}' з БД: {e}", exc_info=True)
        else:
            logger.info(f"Сесія '{self.session_id}' не знайдена в БД. Буде створена нова.")

    def save(self):
        logger.debug(f"Entering CustomDBSessionString.save() for session '{self.session_id}'.")
        if not self.db_pool:
            logger.warning("DB pool not set for CustomDBSessionString. Cannot save session.")
            return

        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                logger.error("No running event loop found during CustomDBSessionString.save. Cannot save session asynchronously.")
                return

        try:
            # ЗМІНЕНО: Викликаємо метод save() базового класу StringSession
            session_string_bytes = super().save().encode('utf-8')
            logger.debug("Successfully called super().save().")
        except AttributeError as e:
            # Цей блок більше не повинен викликатися, але залишаємо для безпеки
            logger.critical(f"AttributeError caught while calling super().save(): {e}", exc_info=True)
            raise e

        if self.api_id is None or self.api_hash is None:
            logger.error(f"Cannot save session '{self.session_id}': API ID or API Hash not set for CustomDBSessionString. Session will not be saved.")
            return

        if self._loop and self._loop.is_running():
            asyncio.create_task(save_telethon_session(
                self.db_pool,
                self.session_id,
                session_string_bytes,
                self.api_id,
                self.api_hash
            ))
            logger.debug(f"Заплановано збереження сесії '{self.session_id}' в БД.")
        else:
            logger.error(f"Cannot save session '{self.session_id}': No running event loop to schedule task. Session will not be saved.")


async def start_telethon_auth_process(callback, state, telethon_manager, get_admin_main_keyboard_func, get_cancel_auth_keyboard_func):
    user_id = callback.from_user.id
    logger.info(f"Запуск логіки авторизації Telethon для користувача {user_id}.")

    await callback.answer("Починаємо авторизацію Telethon...", show_alert=False)

    if telethon_manager.is_main_client_authorized():
        await callback.message.answer(
            "Telethon клієнт вже авторизований. Якщо хочете перевидати сесію, спочатку відключіться.",
            reply_markup=get_admin_main_keyboard_func()
        )
        await state.clear()
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    db_pool = await get_db_pool()
    session_name_placeholder = 'refridex_main_phone_placeholder'

    session = CustomDBSessionString(session_name_placeholder, db_pool, config.api_id, config.api_hash)
    await session.load()

    temp_client = TelegramClient(
        session=session,
        api_id=config.api_id,
        api_hash=config.api_hash,
        system_version="4.16.30-arm64-v8a",
        device_model="Refridex Aiogram Bot",
        app_version="Refridex Bot 1.0"
    )

    try:
        await temp_client.connect()

        if await temp_client.is_user_authorized():
            user_info = await temp_client.get_me()
            temp_client.session.session_id = user_info.phone
            logger.info("Telethon клієнт вже авторизований за збереженою сесією.")
            await telethon_manager.set_main_client(temp_client)
            await callback.message.answer(
                "Telethon клієнт успішно авторизований за збереженою сесією!",
                reply_markup=get_admin_main_keyboard_func()
            )
            await state.clear()
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass
            return

        await state.update_data(telethon_temp_client=temp_client, db_pool=db_pool)
        await state.set_state('TelethonAuthStates:waiting_for_phone')
        await callback.message.answer(
            "Будь ласка, надішліть номер телефону для авторизації Telethon у форматі `+380XXXXXXXXX` (без пробілів):",
            reply_markup=get_cancel_auth_keyboard_func()
        )
        logger.info(f"Користувач {user_id} переведений у стан очікування номера телефону.")

    except Exception as e:
        logger.error(f"Помилка ініціалізації Telethon клієнта: {e}", exc_info=True)
        await callback.message.answer(
            f"Помилка ініціалізації Telethon: {e}. Спробуйте знову.",
            reply_markup=get_admin_main_keyboard_func()
        )
        await state.clear()
        if temp_client.is_connected():
            await temp_client.disconnect()
        logger.info(f"Користувачу {user_id} надіслано повідомлення про помилку ініціалізації Telethon.")


async def cli_telethon_auth_process():
    print("--- Авторизація Telethon сесії через командний рядок (з БД) ---")
    print("Цей режим призначений для первинної авторизації або перевипуску сесії.")
    print("Після успішної авторизації сесія буде збережена в базі даних.")

    print("Ініціалізація пулу підключень до БД...")
    logging.getLogger().setLevel(logging.WARNING)

    await create_db_pool()
    db_pool = await get_db_pool()
    if not db_pool:
        print("Помилка: Не вдалося ініціалізувати пул підключень до бази даних.")
        sys.exit(1)

    print("Перевірка/створення таблиць бази даних...")
    await init_db_tables()

    api_id = config.api_id
    api_hash = config.api_hash

    if not api_id or not api_hash:
        print("Помилка: API_ID або API_HASH не завантажено з config.py. Перевірте ваш .env та config.py.")
        print("Будь ласка, введіть їх вручну:")
        try:
            api_id = int(input("Ваш API ID: "))
            api_hash = input("Ваш API Hash: ")
        except ValueError:
            print("Некоректний API ID. Це має бути число.")
            await close_db_pool()
            sys.exit(1)

    temp_session_id = 'cli_temp_session_placeholder'

    session = CustomDBSessionString(temp_session_id, db_pool, api_id, api_hash)
    await session.load()

    client = TelegramClient(
        session=session,
        api_id=api_id,
        api_hash=api_hash,
        system_version="4.16.30-arm64-v8a",
        device_model="Refridex CLI Auth Tool",
        app_version="Refridex CLI Auth 1.0"
    )

    print("Підключаємося до Telegram...")
    try:
        await client.connect()

        if await client.is_user_authorized():
            user_info = await client.get_me()
            client.session.session_id = user_info.phone
            print(f"✅ Telethon клієнт вже авторизований як: {user_info.first_name} {user_info.last_name or ''} (@{user_info.username}) ID: {user_info.id}")
            print(f"Сесія для {user_info.phone} знайдена та успішно завантажена з бази даних.")
        else:
            print("Потрібна авторизація. Будь ласка, введіть дані:")
            phone_number = input("Номер телефону (у форматі +380XXXXXXXXX): ").strip()
            if not phone_number.startswith('+') or not phone_number[1:].isdigit():
                print("Некоректний формат номера телефону. Він має починатися з '+' та містити лише цифри.")
                await client.disconnect()
                await close_db_pool()
                sys.exit(1)

            client.session.session_id = phone_number

            try:
                print(f"Надсилаємо код підтвердження на {phone_number}...")
                sent_code = await client.send_code_request(phone_number)
                print("Код відправлено. Перевірте Telegram (офіційний додаток або СМС).")

                phone_code = input("Введіть отриманий код: ").strip()

                print("Намагаємося увійти з кодом...")
                await client.sign_in(phone=phone_number, code=phone_code, phone_code_hash=sent_code.phone_code_hash)
                user_info = await client.get_me()
                print(f"✅ Успішна авторизація! Ви увійшли як: {user_info.first_name} {user_info.last_name or ''} (@{user_info.username}) ID: {user_info.id}")
                print(f"Сесія для {user_info.phone} успішно збережена в базі даних.")

            except SessionPasswordNeededError:
                print("Потрібен 2FA пароль (хмарний пароль).")
                password = input("Введіть ваш 2FA пароль: ").strip()
                try:
                    await client.sign_in(password=password)
                    user_info = await client.get_me()
                    print(f"✅ Успішна авторизація з 2FA! Ви увійшли як: {user_info.first_name} {user_info.last_name or ''} (@{user_info.username}) ID: {user_info.id}")
                    print(f"Сесія для {user_info.phone} успішно збережена в базі даних.")
                except Exception as e:
                    print(f"❌ Помилка авторизації з паролем: {e}")
            except PhoneCodeExpiredError:
                print("❌ Термін дії коду минув. Будь ласка, спробуйте знову, ввівши код швидше.")
            except PhoneCodeInvalidError:
                print("❌ Неправильний код. Будь ласка, перевірте і спробуйте знову.")
            except PhoneCodeEmptyError:
                print("❌ Ви ввели порожній код. Будь ласка, спробуйте знову.")
            except FloodWaitError as e:
                print(f"❌ Забагато спроб. Будь ласка, спробуйте через {e.seconds} секунд.")
            except RPCError as e:
                print(f"❌ Помилка Telegram API: {e} (Code: {e.code})")
            except Exception as e:
                print(f"❌ Неочікувана помилка під час авторизації: {e}")

    finally:
        if client.is_connected():
            await client.disconnect()
        await close_db_pool()
        print("\nКлієнт Telethon відключено, пул БД закрито.")

if __name__ == "__main__":
    try:
        asyncio.run(cli_telethon_auth_process())
    except KeyboardInterrupt:
        print("\nОперація скасована користувачем.")
    except Exception as e:
        print(f"\nКритична помилка виконання: {e}")
        sys.exit(1)