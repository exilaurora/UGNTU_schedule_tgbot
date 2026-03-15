# 🧭 RaspBot — Telegram-бот расписания УГНТУ

**RaspBot** — это асинхронный Telegram-бот, позволяющий студентам УГНТУ получать актуальное расписание прямо в Telegram.  
Бот поддерживает выбор подгруппы, работу с несколькими группами и кэширование при недоступности сервера.

---

## ✨ Возможности

- 🔍 Поиск и выбор групп по названию
- 👥 Поддержка подгрупп
- 🗓️ Просмотр расписания на сегодня, завтра или другой день
- 🔁 Отслеживание нескольких групп одновременно
- 💾 Кэширование расписания при недоступности API
- 🧠 Хранение состояний и данных в **MongoDB**
- ⚙️ Полностью асинхронный стек: `aiogram`, `aiohttp`, `motor`
- ✉️ Поддержка inline query

---

## ⚙️ Сборка и запуск

### 🐧 Linux

```bash
git clone git@github.com:exilaurora/UGNTU_schedule_tgbot.git rasp_bot

cd rasp_bot

chmod +x build.sh
./build.sh
```

> Скрипт соберёт Docker-образ.

---

### 🪟 Windows

```powershell
git clone git@github.com:exilaurora/UGNTU_schedule_tgbot.git rasp_bot

cd rasp_bot

docker build -t rasp_bot .
```

> Убедитесь, что **Docker Desktop** установлен и запущен.

---

### 🍎 macOS

```bash
git clone git@github.com:exilaurora/UGNTU_schedule_tgbot.git rasp_bot

cd rasp_bot

docker build -t rasp_bot .
```

> Можно использовать [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
> или [Colima](https://github.com/abiosoft/colima) как альтернативу.

---

## 🐳 Пример `docker-compose.yml`

Для запуска используйте команду
```bash
docker compose up -d
```

`docker-compose.yaml`
```yaml
services:
  rasp_bot:
    image: ghcr.io/exilaurora/ugntu_schedule_tgbot:latest
    container_name: rasp_bot
    volumes:
      - ./src:/usr/src/app
    working_dir: /usr/src/app
    environment:
      - MONGO_HOST=mongo
      - MONGO_PORT=27017
      - MONGO_USER=myuser
      - MONGO_PASSWORD=mypassword
      - MONGO_DB=mydatabase
      - BOT_TOKEN=YOUR_TOKEN
      - ADMIN_USERID=1234567
    depends_on:
      - mongo
    networks:
      - rasp_bot_net

  mongo:
    image: mongo:7
    container_name: mongo_db
    restart: always
    environment:
      - MONGO_INITDB_ROOT_USERNAME=root
      - MONGO_INITDB_ROOT_PASSWORD=rootpassword
      - MONGO_INITDB_DATABASE=mydatabase
    volumes:
      - mongo_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    networks:
      - rasp_bot_net

volumes:
  mongo_data:

networks:
  rasp_bot_net:
    driver: bridge
```

---

## 🔑 Переменные окружения

| Переменная       | Описание                                                               |
| ---------------- | ---------------------------------------------------------------------- |
| `BOT_TOKEN`      | Токен Telegram-бота, полученный у [@BotFather](https://t.me/BotFather) |
| `MONGO_HOST`     | Адрес MongoDB                                                          |
| `MONGO_PORT`     | Порт MongoDB (по умолчанию `27017`)                                    |
| `MONGO_USER`     | Имя пользователя базы                                                  |
| `MONGO_PASSWORD` | Пароль                                                                 |
| `MONGO_DB`       | Имя базы данных                                                        |
| `ADMIN_USERID`   | UserID админа. Нужно для доступа к команде `/BreakAPI`                 |

---

## 📂 Структура проекта

```
src/
 ├── handlers/              # Обработчики команд и callback-запросов
 ├── filters/               # Кастомные фильтры для aiogram
 ├── states/                # FSM-состояния пользователей
 ├── keyboards/             # Инлайн и реплай клавиатуры
 ├── rusoil_api.py          # Асинхронная обёртка API расписания
 ├── main.py                # Точка входа
 └── build.sh               # Скрипт сборки Docker-образа (Linux)
```

---

## 🚀 Быстрый старт (без Docker)

1. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```
2. Настройте переменные окружения или `.env`
3. Запустите бота:

   ```bash
   python3 ./src/main.py
   ```

---

## 🧩 Пример использования в Telegram

```
/start
```

> Введите свою группу и подгруппу, чтобы бот показал расписание на сегодня.
> Позже вы можете изменить группу или просматривать расписание других групп.

---

## 🧑‍💻 Автор

**ExilAurora**
📧 [contact@exilaurora.ru](mailto:contact@exilaurora.ru)
🌐 [github.com/ExilAurora](https://github.com/ExilAurora)

---

## 🪪 Лицензия

Этот проект распространяется под лицензией **GNU GPL-3.0**.
Вы можете свободно использовать, изменять и распространять код при условии сохранения исходной лицензии.

```
GNU General Public License v3.0
https://www.gnu.org/licenses/gpl-3.0.html
```

---

💡 *Если хотите внести вклад — создайте pull request или issue в репозитории проекта!*
