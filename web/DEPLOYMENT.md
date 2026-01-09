# Инструкция по развертыванию TGBotStat

## Структура проекта

```
TGBotStat/
├── main.py              # Точка входа приложения (NiceGUI)
├── web/
│   ├── index.html       # Посадочная страница
│   ├── nginx.conf       # Конфигурация Nginx
│   └── apache.conf      # Конфигурация Apache
├── core/                # Бизнес-логика
├── ui/                  # UI-компоненты
└── requirements.txt     # Зависимости Python
```

## Как это работает

1. **index.html** - статическая посадочная страница, которая:
   - Показывается на корневом пути (`/`), когда пользователь заходит на сайт
   - Автоматически проверяет доступность приложения
   - Перенаправляет на `/app`, когда приложение запущено
   - Показывает сообщение об ошибке, если приложение не запущено

2. **main.py** - запускает NiceGUI на порту 8080

3. **Веб-сервер (Nginx/Apache)** - проксирует запросы:
   - Корневой путь (`/`) обслуживает статический `index.html`
   - Путь `/app` проксируется к NiceGUI на порту 8080
   - Путь `/_nicegui` проксируется к NiceGUI (для статических файлов и WebSocket)

## Развертывание с Nginx

### 1. Установите зависимости

```bash
pip install -r requirements.txt
```

### 2. Настройте Nginx

Скопируйте конфигурацию:
```bash
sudo cp web/nginx.conf /etc/nginx/sites-available/tgbotstat
```

Отредактируйте файл, заменив:
- `your-domain.com` на ваш домен или IP
- `/path/to/TGBotStat/web` на реальный путь к проекту

Активируйте сайт:
```bash
sudo ln -s /etc/nginx/sites-available/tgbotstat /etc/nginx/sites-enabled/
sudo nginx -t  # Проверка конфигурации
sudo systemctl reload nginx
```

### 3. Запустите приложение

```bash
python main.py
```

Или используйте systemd для автозапуска (см. ниже).

## Развертывание с Apache

### 1. Установите зависимости

```bash
pip install -r requirements.txt
```

### 2. Настройте Apache

Скопируйте конфигурацию:
```bash
sudo cp web/apache.conf /etc/apache2/sites-available/tgbotstat.conf
```

Отредактируйте файл, заменив:
- `your-domain.com` на ваш домен или IP
- `/path/to/TGBotStat/web` на реальный путь к проекту

Включите необходимые модули:
```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod rewrite
sudo a2enmod headers
```

Активируйте сайт:
```bash
sudo a2ensite tgbotstat
sudo apache2ctl configtest  # Проверка конфигурации
sudo systemctl reload apache2
```

### 3. Запустите приложение

```bash
python main.py
```

## Автозапуск с systemd

Создайте файл `/etc/systemd/system/tgbotstat.service`:

```ini
[Unit]
Description=TGBotStat Telegram Analytics
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/TGBotStat
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /path/to/TGBotStat/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Замените `/path/to/TGBotStat` на реальный путь.

Активируйте сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable tgbotstat
sudo systemctl start tgbotstat
```

Проверка статуса:
```bash
sudo systemctl status tgbotstat
```

## Проверка работы

1. Откройте браузер и перейдите на ваш домен
2. Если приложение не запущено, вы увидите посадочную страницу с сообщением "Приложение не запущено"
3. Если приложение запущено, вы автоматически будете перенаправлены на интерфейс приложения

## Важные замечания

- NiceGUI работает на порту 8080 (можно изменить в `main.py`)
- Веб-сервер должен быть настроен на проксирование к этому порту
- Убедитесь, что порт 8080 не доступен извне (только через прокси)
- Для продакшена рекомендуется использовать HTTPS (Let's Encrypt)
