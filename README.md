# ProfanityBot

---
### ***Telegram-бот, который следит за своей речью.***
В данном репозитории лежит код Telegram-бота @prfnt_bot, который следит за
красотой речи в чате и выписывает штрафы за её порчу.

---
### ***Функционал бота***
Анализирует весь входящий текст, голосовые сообщения и видео-заметки на предмет обсценной лексики.
При обнаружении таковой в речи добавляет количество обнаруженного мата в таблицу /curses.

Также существует дополнительный функционал, который можно разрешить в боте.
Смотрите полный список команд для подробной информации.

---
### ***Команды, которые доступны в боте:***
Смотрите полный список команд, как и их описание и доступ в самом боте или handle_commands.py.

---
### ***Псевдокоманды, которые доступны в боте***
Набор некоторых подстрок, на которые реагирует бот.
- ***/сурсе*** - отправляет случайный стикер, гифку или фото.
- ***сосал*** - отправляет ответное "сосал"
- ***Я*** и ***проиграл*** в одном сообщении - отправляет ответное "я проиграл"

---
### ***Стек технологий***
- Python
  - python-telegram-bot
  - numpy
  - pandas
  - scipy
  - scikit-learn
  - imbalanced-learn
  - sqlite3 (Можно использовать другую базу данных, такую как PostgreSQL или MySQL)
- ffmpeg
- Docker
  - Docker-compose
- Git :)

---
### ***Файлы, которые есть в репозитории:***
<pre>
ProfanityBot/
├── core/
│   ├── analysis/
│   │   ├── messages.py
│   │   ├── speech_recognition.py
│   │   └── textutil.py
│   ├── data_access/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── logs.py
│   ├── IO/
│   │   ├── handle_commands.py
│   │   ├── handle_functions.py
│   │   └── main.py
│   └── model_workshop/
│       ├── <span style="color:yellow">profanity_pipeline</span>
│       ├── <span style="color:yellow">whisper</span>
│       └── model_training
├── <span style="color:red">data</span>
├── <span style="color:yellow">media</span>
├── <span style="color:yellow">media_nightly</span>
├── <span style="color:yellow">safe</span>
├── <span style="color:cyan">.dockerignore</span>
├── <span style="color:red">.e</span><span style="color:cyan">nv</span>
├── <span style="color:orange">.gitignore</span>
├── <span style="color:cyan">docker-compose.yaml</span>
├── <span style="color:cyan">Dockerfile</span>
├── <span style="color:orange">README.md</span>
└── requirements.txt
</pre>

### ***Легенда:***
<pre>
<span style="color:red">Красный</span> - файл относится к чувствительной информации и не появится в репозитории. Если не имеет других цветов, то обязателен для работы.
<span style="color:yellow">Желтый</span> - файл используется для хранения данных, которые либо много занимают памяти, либо могут быть настроены (подробности ниже).
<span style="color:cyan">Бирюзовый</span> - файл относится к Docker и Docker-compose, и не обязателен, если хотите запускать его на своем ПК.
<span style="color:orange">Оранжевый</span> - файл относится к Git и GitHub и не обязателен.
<span style="color:red">Несколько</span> <span style="color:yellow">цветов</span> <span style="color:cyan">одновременно</span> - относится к указанным категориям.
Без цвета - файл обязателен для работы.
</pre>

### ***Памятка:***
- ***profanity_pipeline*** - содержит в себе модели для категоризации слов на мат и нормальные слова. Используется в model_training.py.
- ***whisper*** - хранилище для моделей OpenAI Whisper для конвертации аудио в текст. Разворачиваются локально, модель, которая используется ботом хранится в data под названием whisperer.pt.
- ***media*** и ***media_nightly*** - хранилище для медиа, которые может отправлять бот.
- ***safe*** - данные для обучения profanity_pipeline. Используются только открытые источники и логи работы бота (В логи идут только сообщения со специального чата. У остальных чатов автоматически установлена настройка приватности, которая не дает попадать сообщениям в логи, и её может изменить только владелец бота.)