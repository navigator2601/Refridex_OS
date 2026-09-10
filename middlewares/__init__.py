"""
middlewares/ - Проміжне програмне забезпечення (Aiogram Middlewares).
Містить:
- db_middleware: прокидання пулу/сесії БД у контекст хендлерів;
- auth_middleware: RBAC-перевірка рівня доступу користувача;
- error_middleware: глобальний захист від виняткових ситуацій.
"""

