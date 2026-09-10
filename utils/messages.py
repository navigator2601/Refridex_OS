# utils/messages.py
"""
utils/messages.py - Централізоване сховище текстових шаблонів та повідомлень бота Refridex OS.
Усі повідомлення, сповіщення та картки користувача зосереджені тут для зручного редагування.
"""
from typing import Optional, List, Any
from database.models.user import UserModel, AccessLevel


class CommonMessages:
    """Загальні повідомлення системи (привітання, довідка, профіль)."""

    @staticmethod
    def welcome(user_name: str, badge: str) -> str:
        return (
            f"👋 Вітаємо в системі <b>Refridex OS</b>, {user_name}!\n\n"
            f"Ваш поточний статус: <b>{badge}</b>\n\n"
            f"Оберіть потрібний розділ у меню нижче:"
        )

    @staticmethod
    def help_text(level: AccessLevel) -> str:
        text = (
            "<b>📖 Довідник рівнів доступу Refridex OS</b>\n\n"
            "• 🔒 <b>Гість [Level 0]:</b> подання заявки на авторизацію, контакти.\n"
        )
        if level >= AccessLevel.TECHNO_NAVIGATOR:
            text += "• 🧭 <b>Техно-Навігатор [L1]:</b> каталог, довідники, пошук, коди помилок, інструкції.\n"
        if level >= AccessLevel.SYSTEM_ENGINEER:
            text += "• 🔧 <b>Системний Інженер [L3]:</b> додаткові інженерні функції, пошук магазинів, список ТТ, завдання, звіти, пробіг.\n"
        if level >= AccessLevel.PROTOCOL_LEAD:
            text += "• 📊 <b>Керівник Протоколів [L6]:</b> координація бригад, розширене зведення та звірка заявок.\n"
        if level >= AccessLevel.CORE_ADMIN:
            text += "• 🛡️ <b>Адміністратор Ядра [L10]:</b> адміністрування системи, редагування нормативних даних та керування ролями.\n"
        if level >= AccessLevel.SYSTEM_ARCHITECT:
            text += "• 🧬 <b>Архітектор Системи [ROOT]:</b> повний контроль серверів, Telethon-сесій та конфігурацій.\n"
        if level >= AccessLevel.AWAKENED:
            text += "• 🌀 <b>Пробуджений Refridex [L∞]:</b> абсолютний доступ та керування всіма потоками системи.\n"

        text += "\nДля виклику функцій використовуйте клавіатуру меню."
        return text

    @staticmethod
    def user_card(user: UserModel) -> str:
        role_badge = user.access_level.badge
        status = "✅ Авторизовано" if user.is_authorized else "⏳ Очікує підтвердження"

        text = (
            f"<b>{role_badge}</b>\n\n"
            f"<b>ID:</b> <code>{user.id}</code>\n"
            f"<b>Користувач:</b> @{user.username if user.username else 'не вказано'}\n"
            f"<b>ПІБ:</b> {user.surname or ''} {user.official_name or user.first_name or ''} {user.patronymic or ''}\n"
            f"<b>Позивний:</b> {user.call_sign or 'не призначено'}\n"
            f"<b>Телефон:</b> {user.phone or 'не вказано'}\n"
            f"<b>Статус:</b> {status}\n"
        )
        if user.access_level.is_admin():
            text += (
                f"\n<b>Права адміністратора:</b>\n"
                f"• Сесії: {'✅' if user.can_manage_sessions else '❌'}\n"
                f"• Чати: {'✅' if user.can_manage_chats else '❌'}\n"
                f"• Користувачі: {'✅' if user.can_manage_users else '❌'}\n"
            )
        return text.strip()

    PROFILE_NOT_FOUND = "⚠️ Не вдалося завантажити профіль. Спробуйте /start"
    PROFILE_EDIT_ALERT = "Зміна позивного та персональних даних здійснюється через адміністратора."
    DATA_UNAVAILABLE = "⚠️ Дані недоступні"
    USER_NOT_FOUND = "Користувача не знайдено"
    DATA_REFRESHED = "✅ Дані оновлено"

    @staticmethod
    def pagination_page(page: int) -> str:
        return f"📄 Меню (сторінка {page}):"


class GuestMessages:
    """Повідомлення для гостей (реєстрація, перевірка статусу, схвалення/відхилення)."""

    CANCELLED = "❌ Дію скасовано. Повернення до головного меню."

    @staticmethod
    def already_authorized(badge: str) -> str:
        return f"✅ Ви вже авторизовані в системі як <b>{badge}</b>."

    REG_STEP_PHONE = (
        "📝 <b>Реєстрація користувача (Крок 1 з 2)</b>\n\n"
        "Будь ласка, надішліть ваш контакт за допомогою кнопки <b>«📱 Поділитися контактом»</b> "
        "нижче або введіть номер телефону вручну (у форматі <code>+380XXXXXXXXX</code>):"
    )

    REG_INVALID_PHONE = (
        "⚠️ Некоректний формат номера телефону.\n"
        "Скористайтеся кнопкою <b>«📱 Поділитися контактом»</b> або введіть номер у форматі: <code>+380XXXXXXXXX</code>"
    )

    @staticmethod
    def reg_step_name(phone: str) -> str:
        return (
            f"✅ Номер телефону зафіксовано: <code>{phone}</code>\n\n"
            "👤 <b>Крок 2 з 2: Ваше ім'я</b>\n\n"
            "Введіть ваше ім'я (як до вас звертатися, наприклад: <i>Олександр</i>):"
        )

    REG_INVALID_NAME = "⚠️ Будь ласка, введіть коректне ім'я (щонайменше 2 літери):"

    @staticmethod
    def reg_success_user(phone: str, name: str) -> str:
        return (
            "🎉 <b>Заявку успішно надіслано!</b>\n\n"
            f"<b>Ім'я:</b> {name}\n"
            f"<b>Телефон:</b> <code>{phone}</code>\n\n"
            "⏳ Вашу анкету передано адміністратору на перевірку. "
            "Щойно доступ буде підтверджено, ви отримаєте повідомлення, а меню автоматично розшириться.\n\n"
            "Ви також можете натиснути «🔄 Перевірити статус» у будь-який час."
        )

    @staticmethod
    def reg_admin_notification(
        username: Optional[str],
        user_id: int,
        name: str,
        phone: str,
    ) -> str:
        return (
            "🔔 <b>Нова заявка на авторизацію!</b>\n\n"
            f"<b>Користувач:</b> @{username or 'немає'}\n"
            f"<b>Telegram ID:</b> <code>{user_id}</code>\n"
            f"<b>Ім'я:</b> {name}\n"
            f"<b>Телефон:</b> <code>{phone}</code>\n\n"
            "Оберіть дію:"
        )

    @staticmethod
    def status_approved(badge: str, name: Optional[str]) -> str:
        return (
            f"🎉 <b>Ваш статус оновлено!</b>\n\n"
            f"Поточний рівень: <b>{badge}</b>\n"
            f"Користувач: <b>{name or 'Авторизовано'}</b>\n\n"
            "Робоче меню активовано нижче:"
        )

    @staticmethod
    def status_pending(name: Optional[str], phone: Optional[str]) -> str:
        return (
            "⏳ <b>Ваша заявка знаходиться на розгляді.</b>\n\n"
            f"Ім'я: <code>{name or 'не вказано'}</code>\n"
            f"Телефон: <code>{phone or 'не вказано'}</code>\n\n"
            "Адміністратор ще не підтвердив доступ. Будь ласка, очікуйте."
        )

    STATUS_NOT_SUBMITTED = (
        "ℹ️ <b>Ви ще не заповнили заявку на реєстрацію.</b>\n\n"
        "Натисніть <b>«📝 Подати заявку на реєстрацію»</b> нижче, щоб отримати доступ монтажника."
    )

    GUEST_HELP_CONTACTS = (
        "<b>📖 Інформація для гостей Refridex OS</b>\n\n"
        "Цей бот призначений для оперативного обліку монтажів кондиціонерів, "
        "розрахунку фреону та формування звітів по торговельних точках.\n\n"
        "<b>Як отримати доступ монтажника:</b>\n"
        "1. Натисніть «📝 Подати заявку на реєстрацію».\n"
        "2. Надішліть номер телефону та ваше ім'я.\n"
        "3. Після схвалення адміністратором вам відкриється повний робочий функціонал.\n\n"
        "📞 З екстрених питань звертайтеся до чергового диспетчера."
    )

    @staticmethod
    def admin_approved_card(original_text: str, badge: str, admin_repr: str) -> str:
        return (
            f"{original_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>СХВАЛЕНО!</b> Надано статус: <b>{badge}</b>\n"
            f"Адміністратор: @{admin_repr}"
        )

    @staticmethod
    def admin_rejected_card(original_text: str, admin_repr: str) -> str:
        return (
            f"{original_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"❌ <b>ВІДХИЛЕНО</b> адміністратором @{admin_repr}"
        )

    @staticmethod
    def user_approved_notify(badge: str) -> str:
        return (
            f"🎉 <b>Вітаємо! Вашу заявку схвалено!</b>\n\n"
            f"Вам надано доступ: <b>{badge}</b>.\n"
            f"Робоче меню активовано. Ви можете приступати до роботи:"
        )

    USER_REJECTED_NOTIFY = (
        "⚠️ <b>Вашу заявку на реєстрацію було відхилено.</b>\n\n"
        "Зверніться до бригадира або диспетчера для уточнення причини."
    )


class MontageMessages:
    """Повідомлення модуля монтажу (заміри, об'єкти)."""

    @staticmethod
    def montage_intro(display_name: str) -> str:
        return (
            f"❄️ <b>Введення замірів магістралей</b>\n\n"
            f"Монтажник: <b>{display_name}</b>\n\n"
            f"Для початку введення оберіть об'єкт зі списку «📍 Мої об'єкти (ТТ)» "
            f"або введіть номер/код торговельної точки (наприклад: <code>А3406</code>)."
        )

    MY_STORES_EMPTY = (
        "📍 <b>Закріплені об'єкти (ТТ)</b>\n\n"
        "Наразі немає активних призначених завдань.\n"
        "Нові завдання з'являтимуться автоматично після обробки заявок у робочих групах."
    )


class AdminMessages:
    """Повідомлення адміністративної панелі."""

    @staticmethod
    def panel_stats(total_users: int, active_sessions: int, allowed_chats: int) -> str:
        return (
            "<b>⚙️ Адміністративна панель Refridex OS</b>\n\n"
            "<b>Статистика системи:</b>\n"
            f"• Зареєстровано користувачів: <b>{total_users}</b>\n"
            f"• Активних Telethon-сесій: <b>{active_sessions}</b>\n"
            f"• Дозволених робочих груп/чатів: <b>{allowed_chats}</b>\n\n"
            "<i>Оберіть потрібну дію в меню адміністрування.</i>"
        )

    USERS_LIST_EMPTY = "👥 Користувачів у системі поки немає."

    @staticmethod
    def users_list(users: List[Any]) -> str:
        lines = ["<b>👥 Останні зареєстровані користувачі:</b>\n"]
        for u in users:
            lvl = AccessLevel(u["access_level"]).badge
            name = f"{u['surname'] or ''} {u['official_name'] or ''}".strip() or (
                f"@{u['username']}" if u['username'] else f"ID: {u['id']}"
            )
            call = f" [{u['call_sign']}]" if u["call_sign"] else ""
            auth = "✅" if u["is_authorized"] else "⏳"
            lines.append(f"{auth} {lvl} {name}{call} (<code>{u['id']}</code>)")

        lines.append("\n<i>Для зміни рівня доступу використовуйте команду /setrole &lt;id&gt; &lt;level&gt;</i>")
        return "\n".join(lines)

    SESSIONS_LIST_EMPTY = "🤖 Жодної Telethon-сесії ще не зареєстровано в базі."

    @staticmethod
    def sessions_list(sessions: List[Any]) -> str:
        lines = ["<b>🤖 Реєстр MTProto-сесій Telethon:</b>\n"]
        for s in sessions:
            status = "🟢 Активна" if (s["is_authorized"] and s["is_active"]) else "🔴 Неактивна / Очікує коду"
            uname = f" (@{s['telegram_username']})" if s['telegram_username'] else ""
            lines.append(f"• <b>{s['phone_number']}</b>{uname}: {status}")
        return "\n".join(lines)

