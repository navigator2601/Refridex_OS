-- telethon_auth.users визначення

-- Drop table

-- DROP TABLE telethon_auth.users;

CREATE TABLE telethon_auth.users (
	id int8 NOT NULL, -- Унікальний числовий ідентифікатор користувача в Telegram (Telegram User ID, PK).
	username varchar(255) NULL, -- Юзернейм користувача в Telegram (без символу @).
	call_sign varchar(100) NULL, -- Внутрішній робочий позивний або код монтажника (напр. ІМ-5, MAN-1), UNIQUE.
	first_name varchar(255) NULL, -- Ім'я користувача, отримане з його профілю в Telegram.
	last_name varchar(255) NULL -- Прізвище користувача, отримане з його профілю в Telegram.,
	surname varchar(100) NULL, -- Офіційне прізвище монтажника для службових звітів і відомостей.
	official_name varchar(100) NULL, -- Офіційне ім'я монтажника для документів.
	patronymic varchar(100) NULL -- По батькові монтажника для офіційних актів та звітів.,
	phone varchar(30) NULL, -- Робочий або контактний номер телефону спеціаліста.
	is_authorized bool DEFAULT false NOT NULL, -- Прапор авторизації: true — користувач пройшов перевірку та допущений до функціоналу.
	is_active bool DEFAULT true NOT NULL, -- Стан активності: true — діючий обліковий запис, false — заблокований або звільнений.
	access_level int2 DEFAULT 0 NOT NULL, -- Рівень доступу: 0=GUEST, 1=NAVIGATOR, 3=ENGINEER, 6=LEAD, 10=ADMIN, 100=ARCHITECT, 101=AWAKENED.
	can_manage_sessions bool DEFAULT false NOT NULL, -- Дозвіл на додавання, видалення та скидання робочих Telethon-сесій.
	can_manage_chats bool DEFAULT false NOT NULL, -- Дозвіл на керування переліком дозволених чатів і каналів (allowed_chats).
	can_manage_users bool DEFAULT false NOT NULL, -- Дозвіл на зміну рівнів доступу та активацію інших користувачів.
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Дата та час створення технічного запису в системі.
	registered_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Дата та час проходження повної реєстрації користувачем.
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Час останнього оновлення даних користувача (оновлюється тригером).
	last_activity timestamptz DEFAULT CURRENT_TIMESTAMP NULL, -- Часова мітка останньої взаємодії користувача з ботом або системою.
	CONSTRAINT chk_users_access_level CHECK (((access_level >= 0) AND (access_level <= 101))),
	CONSTRAINT users_call_sign_key UNIQUE (call_sign),
	CONSTRAINT users_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_users_access_level ON telethon_auth.users USING btree (access_level);
CREATE INDEX idx_users_username ON telethon_auth.users USING btree (username);
COMMENT ON TABLE telethon_auth.users IS 'Користувачі Telegram-бота: облікові дані, профіль монтажника та інтегровані права доступу.';

-- Column comments

COMMENT ON COLUMN telethon_auth.users.id IS 'Унікальний числовий ідентифікатор користувача в Telegram (Telegram User ID, PK).';
COMMENT ON COLUMN telethon_auth.users.username IS 'Юзернейм користувача в Telegram (без символу @).';
COMMENT ON COLUMN telethon_auth.users.call_sign IS 'Внутрішній робочий позивний або код монтажника (напр. ІМ-5, MAN-1), UNIQUE.';
COMMENT ON COLUMN telethon_auth.users.first_name IS 'Ім''я користувача, отримане з його профілю в Telegram.';
COMMENT ON COLUMN telethon_auth.users.last_name IS 'Прізвище користувача, отримане з його профілю в Telegram.';
COMMENT ON COLUMN telethon_auth.users.surname IS 'Офіційне прізвище монтажника для службових звітів і відомостей.';
COMMENT ON COLUMN telethon_auth.users.official_name IS 'Офіційне ім''я монтажника для документів.';
COMMENT ON COLUMN telethon_auth.users.patronymic IS 'По батькові монтажника для офіційних актів та звітів.';
COMMENT ON COLUMN telethon_auth.users.phone IS 'Робочий або контактний номер телефону спеціаліста.';
COMMENT ON COLUMN telethon_auth.users.is_authorized IS 'Прапор авторизації: true — користувач пройшов перевірку та допущений до функціоналу.';
COMMENT ON COLUMN telethon_auth.users.is_active IS 'Стан активності: true — діючий обліковий запис, false — заблокований або звільнений.';
COMMENT ON COLUMN telethon_auth.users.access_level IS 'Рівень доступу в системі: 0=GUEST, 1=USER, 2=MODERATOR, 3=ADMIN (CHECK 0..3).';
COMMENT ON COLUMN telethon_auth.users.can_manage_sessions IS 'Дозвіл на додавання, видалення та скидання робочих Telethon-сесій.';
COMMENT ON COLUMN telethon_auth.users.can_manage_chats IS 'Дозвіл на керування переліком дозволених чатів і каналів (allowed_chats).';
COMMENT ON COLUMN telethon_auth.users.can_manage_users IS 'Дозвіл на зміну рівнів доступу та активацію інших користувачів.';
COMMENT ON COLUMN telethon_auth.users.created_at IS 'Дата та час створення технічного запису в системі.';
COMMENT ON COLUMN telethon_auth.users.registered_at IS 'Дата та час проходження повної реєстрації користувачем.';
COMMENT ON COLUMN telethon_auth.users.updated_at IS 'Час останнього оновлення даних користувача (оновлюється тригером).';
COMMENT ON COLUMN telethon_auth.users.last_activity IS 'Часова мітка останньої взаємодії користувача з ботом або системою.';

-- Table Triggers

CREATE TRIGGER update_users_timestamp BEFORE UPDATE ON telethon_auth.users FOR EACH ROW EXECUTE FUNCTION telethon_auth.update_timestamp();

-- Permissions

ALTER TABLE telethon_auth.users OWNER TO postgres;
GRANT ALL ON TABLE telethon_auth.users TO postgres;
GRANT SELECT, DELETE, INSERT, UPDATE ON TABLE telethon_auth.users TO kondiki;


-- telethon_auth.access_level_history визначення

-- Drop table

-- DROP TABLE telethon_auth.access_level_history;

CREATE TABLE telethon_auth.access_level_history (
	id serial4 NOT NULL, -- Унікальний ідентифікатор запису журналу змін (PK).
	user_id int8 NOT NULL, -- FK до telethon_auth.users — користувач, чий рівень доступу було змінено.
	old_access_level int2 NULL, -- Попередній рівень доступу до виконання зміни (0=GUEST..3=ADMIN).
	new_access_level int2 NOT NULL, -- Новий призначений рівень доступу (0=GUEST..3=ADMIN).
	changed_by_user_id int8 NULL, -- FK до telethon_auth.users — адміністратор, який виконав зміну прав.
	reason text NULL, -- Текстова причина коригування дозволів (для аудиту безпеки).
	changed_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Точний час фіксації зміни рівня доступу.
	CONSTRAINT access_level_history_pkey PRIMARY KEY (id),
	CONSTRAINT chk_hist_new_level CHECK (((new_access_level >= 0) AND (new_access_level <= 101))),
	CONSTRAINT fk_access_history_changed_by FOREIGN KEY (changed_by_user_id) REFERENCES telethon_auth.users(id) ON DELETE SET NULL,
	CONSTRAINT fk_access_history_user_id FOREIGN KEY (user_id) REFERENCES telethon_auth.users(id) ON DELETE CASCADE
);
CREATE INDEX idx_access_history_changed_by ON telethon_auth.access_level_history USING btree (changed_by_user_id);
CREATE INDEX idx_access_history_user_changed ON telethon_auth.access_level_history USING btree (user_id, changed_at DESC);
COMMENT ON TABLE telethon_auth.access_level_history IS 'Журнал аудиту змін рівнів доступу та ролей користувачів.';

-- Column comments

COMMENT ON COLUMN telethon_auth.access_level_history.id IS 'Унікальний ідентифікатор запису журналу змін (PK).';
COMMENT ON COLUMN telethon_auth.access_level_history.user_id IS 'FK до telethon_auth.users — користувач, чий рівень доступу було змінено.';
COMMENT ON COLUMN telethon_auth.access_level_history.old_access_level IS 'Попередній рівень доступу до виконання зміни (0=GUEST..3=ADMIN).';
COMMENT ON COLUMN telethon_auth.access_level_history.new_access_level IS 'Новий призначений рівень доступу (0=GUEST..3=ADMIN).';
COMMENT ON COLUMN telethon_auth.access_level_history.changed_by_user_id IS 'FK до telethon_auth.users — адміністратор, який виконав зміну прав.';
COMMENT ON COLUMN telethon_auth.access_level_history.reason IS 'Текстова причина коригування дозволів (для аудиту безпеки).';
COMMENT ON COLUMN telethon_auth.access_level_history.changed_at IS 'Точний час фіксації зміни рівня доступу.';

-- Permissions

ALTER TABLE telethon_auth.access_level_history OWNER TO postgres;
GRANT ALL ON TABLE telethon_auth.access_level_history TO postgres;
GRANT SELECT, DELETE, INSERT, UPDATE ON TABLE telethon_auth.access_level_history TO kondiki;


-- telethon_auth.allowed_chats визначення

-- Drop table

-- DROP TABLE telethon_auth.allowed_chats;

CREATE TABLE telethon_auth.allowed_chats (
	id serial4 NOT NULL, -- Унікальний числовий ідентифікатор дозволеного чату в базі (PK).
	telegram_chat_id int8 NOT NULL, -- Унікальний ID чату або супергрупи у Telegram (int8, UNIQUE).
	chat_title varchar(255) NULL, -- Назва чату або каналу, як вона відображається в Telegram.
	chat_type varchar(50) NULL, -- Тип спільноти: group, supergroup або channel.
	username varchar(255) NULL, -- Публічний юзернейм або посилання на чат/канал (якщо публічний).
	description text NULL, -- Службовий опис призначення чату (напр. чат монтажників регіону, звітний канал).
	added_by_user_id int8 NULL, -- FK до telethon_auth.users — адміністратор, який додав чат до білого списку.
	is_allowed bool DEFAULT true NOT NULL, -- Прапор дозволу: true — робота дозволена, false — чат тимчасово відключено.
	added_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Дата та час додавання чату до списку.
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Час останнього редагування параметрів чату (оновлюється тригером).
	CONSTRAINT allowed_chats_pkey PRIMARY KEY (id),
	CONSTRAINT allowed_chats_telegram_chat_id_key UNIQUE (telegram_chat_id),
	CONSTRAINT fk_allowed_chats_added_by FOREIGN KEY (added_by_user_id) REFERENCES telethon_auth.users(id) ON DELETE SET NULL
);
CREATE INDEX idx_allowed_chats_is_allowed ON telethon_auth.allowed_chats USING btree (is_allowed);
COMMENT ON TABLE telethon_auth.allowed_chats IS 'Реєстр дозволених груп, каналів та чатів для роботи клієнтів Telethon.';

-- Column comments

COMMENT ON COLUMN telethon_auth.allowed_chats.id IS 'Унікальний числовий ідентифікатор дозволеного чату в базі (PK).';
COMMENT ON COLUMN telethon_auth.allowed_chats.telegram_chat_id IS 'Унікальний ID чату або супергрупи у Telegram (int8, UNIQUE).';
COMMENT ON COLUMN telethon_auth.allowed_chats.chat_title IS 'Назва чату або каналу, як вона відображається в Telegram.';
COMMENT ON COLUMN telethon_auth.allowed_chats.chat_type IS 'Тип спільноти: group, supergroup або channel.';
COMMENT ON COLUMN telethon_auth.allowed_chats.username IS 'Публічний юзернейм або посилання на чат/канал (якщо публічний).';
COMMENT ON COLUMN telethon_auth.allowed_chats.description IS 'Службовий опис призначення чату (напр. чат монтажників регіону, звітний канал).';
COMMENT ON COLUMN telethon_auth.allowed_chats.added_by_user_id IS 'FK до telethon_auth.users — адміністратор, який додав чат до білого списку.';
COMMENT ON COLUMN telethon_auth.allowed_chats.is_allowed IS 'Прапор дозволу: true — робота дозволена, false — чат тимчасово відключено.';
COMMENT ON COLUMN telethon_auth.allowed_chats.added_at IS 'Дата та час додавання чату до списку.';
COMMENT ON COLUMN telethon_auth.allowed_chats.updated_at IS 'Час останнього редагування параметрів чату (оновлюється тригером).';

-- Table Triggers

CREATE TRIGGER update_allowed_chats_timestamp BEFORE UPDATE ON telethon_auth.allowed_chats FOR EACH ROW EXECUTE FUNCTION telethon_auth.update_timestamp();

-- Permissions

ALTER TABLE telethon_auth.allowed_chats OWNER TO postgres;
GRANT ALL ON TABLE telethon_auth.allowed_chats TO postgres;
GRANT SELECT, DELETE, INSERT, UPDATE ON TABLE telethon_auth.allowed_chats TO kondiki;


-- telethon_auth.sessions визначення

-- Drop table

-- DROP TABLE telethon_auth.sessions;

CREATE TABLE telethon_auth.sessions (
	id serial4 NOT NULL, -- Унікальний ідентифікатор сесії в базі (PK).
	phone_number varchar(30) NOT NULL, -- Номер телефону Telegram-акаунта сесії у міжнародному форматі (UNIQUE).
	session_string text NOT NULL, -- Авторизаційний рядок Telethon (StringSession) для підключення без повторного коду.
	api_id int4 NOT NULL, -- Ідентифікатор Telegram API (api_id з my.telegram.org).
	api_hash varchar(255) NOT NULL, -- Секретний хеш додатку Telegram API (api_hash).
	user_id int8 NULL, -- FK до telethon_auth.users — користувач системи, якому закріплено або належить ця сесія.
	is_authorized bool DEFAULT false NOT NULL, -- Статус авторизації: true — сесія успішно увійшла та валідна в Telegram.
	is_active bool DEFAULT true NOT NULL, -- Прапор активності: true — сесія готова до надсилання/зчитування повідомлень.
	telegram_user_id int8 NULL, -- Telegram ID акаунта, під яким запущена ця сесія.
	telegram_username varchar(255) NULL, -- Юзернейм акаунта в Telegram, прив'язаного до даної сесії.
	telegram_first_name varchar(255) NULL -- Ім'я акаунта в Telegram для цієї сесії.,
	telegram_last_name varchar(255) NULL, -- Прізвище акаунта в Telegram для цієї сесії.
	last_login timestamptz DEFAULT CURRENT_TIMESTAMP NULL, -- Часова мітка останнього успішного підключення або оновлення сесії.
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Дата первинного внесення сесії до бази.
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Час останнього оновлення параметрів сесії (оновлюється тригером).
	CONSTRAINT sessions_phone_number_key UNIQUE (phone_number),
	CONSTRAINT sessions_pkey PRIMARY KEY (id),
	CONSTRAINT fk_sessions_user_id FOREIGN KEY (user_id) REFERENCES telethon_auth.users(id) ON DELETE SET NULL
);
CREATE INDEX idx_sessions_active_auth ON telethon_auth.sessions USING btree (is_active, is_authorized);
CREATE INDEX idx_sessions_user_id ON telethon_auth.sessions USING btree (user_id);
COMMENT ON TABLE telethon_auth.sessions IS 'Авторизаційні сесії Telethon-клієнтів (облікові записи Telegram).';

-- Column comments

COMMENT ON COLUMN telethon_auth.sessions.id IS 'Унікальний ідентифікатор сесії в базі (PK).';
COMMENT ON COLUMN telethon_auth.sessions.phone_number IS 'Номер телефону Telegram-акаунта сесії у міжнародному форматі (UNIQUE).';
COMMENT ON COLUMN telethon_auth.sessions.session_string IS 'Авторизаційний рядок Telethon (StringSession) для підключення без повторного коду.';
COMMENT ON COLUMN telethon_auth.sessions.api_id IS 'Ідентифікатор Telegram API (api_id з my.telegram.org).';
COMMENT ON COLUMN telethon_auth.sessions.api_hash IS 'Секретний хеш додатку Telegram API (api_hash).';
COMMENT ON COLUMN telethon_auth.sessions.user_id IS 'FK до telethon_auth.users — користувач системи, якому закріплено або належить ця сесія.';
COMMENT ON COLUMN telethon_auth.sessions.is_authorized IS 'Статус авторизації: true — сесія успішно увійшла та валідна в Telegram.';
COMMENT ON COLUMN telethon_auth.sessions.is_active IS 'Прапор активності: true — сесія готова до надсилання/зчитування повідомлень.';
COMMENT ON COLUMN telethon_auth.sessions.telegram_user_id IS 'Telegram ID акаунта, під яким запущена ця сесія.';
COMMENT ON COLUMN telethon_auth.sessions.telegram_username IS 'Юзернейм акаунта в Telegram, прив''язаного до даної сесії.';
COMMENT ON COLUMN telethon_auth.sessions.telegram_first_name IS 'Ім''я акаунта в Telegram для цієї сесії.';
COMMENT ON COLUMN telethon_auth.sessions.telegram_last_name IS 'Прізвище акаунта в Telegram для цієї сесії.';
COMMENT ON COLUMN telethon_auth.sessions.last_login IS 'Часова мітка останнього успішного підключення або оновлення сесії.';
COMMENT ON COLUMN telethon_auth.sessions.created_at IS 'Дата первинного внесення сесії до бази.';
COMMENT ON COLUMN telethon_auth.sessions.updated_at IS 'Час останнього оновлення параметрів сесії (оновлюється тригером).';

-- Table Triggers

CREATE TRIGGER update_sessions_timestamp BEFORE UPDATE ON telethon_auth.sessions FOR EACH ROW EXECUTE FUNCTION telethon_auth.update_timestamp();

-- Permissions

ALTER TABLE telethon_auth.sessions OWNER TO postgres;
GRANT ALL ON TABLE telethon_auth.sessions TO postgres;
GRANT SELECT, DELETE, INSERT, UPDATE ON TABLE telethon_auth.sessions TO kondiki;


-- telethon_auth.auth_log визначення

-- Drop table

-- DROP TABLE telethon_auth.auth_log;

CREATE TABLE telethon_auth.auth_log (
	id serial4 NOT NULL, -- Унікальний ідентифікатор запису журналу спроби входу (PK).
	user_id int8 NULL, -- FK до telethon_auth.users — користувач, який виконував спробу авторизації.
	phone_number varchar(30) NULL, -- Номер телефону, з якого або на який запитувався код авторизації.
	session_id int4 NULL, -- FK до telethon_auth.sessions — цільова сесія, в межах якої відбувалася спроба.
	auth_status telethon_auth.auth_status_enum NOT NULL, -- Статус спроби авторизації: SUCCESS, FAILED, EXPIRED або REVOKED (ENUM).
	error_message text NULL, -- Текст технічної помилки у разі невдалої авторизації (Failed/Expired).
	ip_address inet NULL, -- IP-адреса клієнта, з якої надійшов запит на авторизацію.
	attempted_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Точний час фіксації спроби авторизації.
	CONSTRAINT auth_log_pkey PRIMARY KEY (id),
	CONSTRAINT fk_auth_log_session_id FOREIGN KEY (session_id) REFERENCES telethon_auth.sessions(id) ON DELETE SET NULL,
	CONSTRAINT fk_auth_log_user_id FOREIGN KEY (user_id) REFERENCES telethon_auth.users(id) ON DELETE SET NULL
);
CREATE INDEX idx_auth_log_attempted_at ON telethon_auth.auth_log USING btree (attempted_at DESC);
CREATE INDEX idx_auth_log_auth_status ON telethon_auth.auth_log USING btree (auth_status);
CREATE INDEX idx_auth_log_user_attempted ON telethon_auth.auth_log USING btree (user_id, attempted_at DESC);
COMMENT ON TABLE telethon_auth.auth_log IS 'Журнал аудиту всіх спроб авторизації та входу користувачів і сесій.';

-- Column comments

COMMENT ON COLUMN telethon_auth.auth_log.id IS 'Унікальний ідентифікатор запису журналу спроби входу (PK).';
COMMENT ON COLUMN telethon_auth.auth_log.user_id IS 'FK до telethon_auth.users — користувач, який виконував спробу авторизації.';
COMMENT ON COLUMN telethon_auth.auth_log.phone_number IS 'Номер телефону, з якого або на який запитувався код авторизації.';
COMMENT ON COLUMN telethon_auth.auth_log.session_id IS 'FK до telethon_auth.sessions — цільова сесія, в межах якої відбувалася спроба.';
COMMENT ON COLUMN telethon_auth.auth_log.auth_status IS 'Статус спроби авторизації: SUCCESS, FAILED, EXPIRED або REVOKED (ENUM).';
COMMENT ON COLUMN telethon_auth.auth_log.error_message IS 'Текст технічної помилки у разі невдалої авторизації (Failed/Expired).';
COMMENT ON COLUMN telethon_auth.auth_log.ip_address IS 'IP-адреса клієнта, з якої надійшов запит на авторизацію.';
COMMENT ON COLUMN telethon_auth.auth_log.attempted_at IS 'Точний час фіксації спроби авторизації.';

-- Permissions

ALTER TABLE telethon_auth.auth_log OWNER TO postgres;
GRANT ALL ON TABLE telethon_auth.auth_log TO postgres;
GRANT SELECT, DELETE, INSERT, UPDATE ON TABLE telethon_auth.auth_log TO kondiki;