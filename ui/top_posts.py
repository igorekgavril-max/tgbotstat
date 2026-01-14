"""
UI компонент: Блок топ-постов
"""
import datetime
from nicegui import ui
from core.state import STATE
from core.services import extract_channel_username
from core.analytics import calculate_er, format_metric

# Словарь функций для сортировки по метрикам
SORT_KEYS = {
    'er': lambda p: p.get('_er', 0),
    'views': lambda p: p.get('views', 0),
    'likes': lambda p: p.get('likes', 0),
    'comments': lambda p: p.get('comments', 0),
    'reposts': lambda p: p.get('reposts', 0),
}


def format_top_posts(posts, channel='', mode='er'):
    """
    Форматирует топ-5 постов по выбранной метрике.
    
    Args:
        posts: Список постов
        channel: Имя канала
        mode: Режим сортировки ('er', 'views', 'likes', 'comments', 'reposts')
    
    Returns:
        str: HTML строка с топ-постами
    """
    if not posts:
        return "<div style='color:#6b7280; padding: 20px; text-align: center;'>Нет постов для отображения</div>"
    
    # Фильтруем посты с просмотрами > 50 (только для ER, для других метрик можно убрать)
    if mode == 'er':
        filtered_posts = [p for p in posts if p.get('views', 0) > 50]
    else:
        filtered_posts = posts.copy() if posts else []
    
    if not filtered_posts:
        return "<div style='color:#6b7280; padding: 20px; text-align: center;'>Нет постов для отображения</div>"
    
    # Убеждаемся, что ER рассчитан для всех постов (если нужно)
    for p in filtered_posts:
        if '_er' not in p:
            views = p.get('views', 0)
            p['_er'] = calculate_er(
                p.get('likes', 0),
                p.get('comments', 0),
                p.get('reposts', 0),
                views
            )
    
    # Сортируем по выбранной метрике
    sort_key = SORT_KEYS.get(mode, SORT_KEYS['er'])
    top_sorted = sorted(filtered_posts, key=sort_key, reverse=True)[:5]
    
    if not top_sorted:
        return "<div style='color:#6b7280; padding: 20px; text-align: center;'>Нет постов для отображения</div>"

    rows = """
    <div style="display:flex; flex-direction:column; gap:12px; width:100%;">
    """

    for i, p in enumerate(top_sorted, start=1):
        # Обрабатываем текст поста
        post_title = p.get('title', '')
        if post_title == "(без текста)" or not post_title:
            text_preview = "Пост без текста..."
        else:
            text_preview = (post_title[:35] + '…') if len(post_title) > 35 else post_title
        
        channel_username = extract_channel_username(channel) if channel else ''
        link = f"https://t.me/{channel_username}/{p['id']}" if channel_username else "#"
        
        # Получаем значение выбранной метрики для отображения
        if mode == 'er':
            metric_value = f"{p.get('_er', 0):.2f}%"
            metric_label = "ER"
        elif mode == 'views':
            metric_value = format_metric(p.get('views', 0))
            metric_label = "Просмотры"
        elif mode == 'likes':
            metric_value = format_metric(p.get('likes', 0))
            metric_label = "Лайки"
        elif mode == 'comments':
            metric_value = format_metric(p.get('comments', 0))
            metric_label = "Комментарии"
        elif mode == 'reposts':
            metric_value = format_metric(p.get('reposts', 0))
            metric_label = "Репосты"
        else:
            metric_value = f"{p.get('_er', 0):.2f}%"
            metric_label = "ER"

        rows += f"""
        <div style="
            display:grid;
            grid-template-columns:
                40px
                minmax(130px, 1fr)
                200px
                200px
                40px;
            gap:16px;
            align-items:center;
            background:#ffffff;
            border:1px solid #e5e7eb;
            border-radius:12px;
            padding:14px 18px;
        ">
            <!-- номер -->
            <div style="font-size:20px; font-weight:700; color:#059669;">
                {i}
            </div>

            <!-- текст -->
            <div style="font-size:14px; font-weight:500; color:#111827; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                {text_preview}
            </div>

            <!-- метрики -->
            <div style="display:flex; gap:18px; font-size:13px; color:#374151;">
                <div><b>{p.get('views', 0)}</b> 👁</div>
                <div><b>{p.get('likes', 0)}</b> 👍</div>
                <div><b>{p.get('comments', 0)}</b> 💬</div>
                <div><b>{p.get('reposts', 0)}</b> 🔁</div>
            </div>

            <!-- Выбранная метрика -->
            <div style="display:flex; font-size:16px; font-weight:700; color:#059669; text-align:center;">
                {metric_label}: {metric_value}
            </div>

            <!-- ссылка -->
            <a href="{link}" target="_blank"
            style="display:flex; text-decoration:none; font-size:18px;">
                🔗
            </a>
        </div>
        """

    rows += "</div>"
    return rows


# Глобальные переменные для хранения компонентов
_metric_buttons = {}
_top_posts_container = None
_css_styles_added = False


def update_top_posts(mode: str):
    """Обновляет отображение топ-постов по выбранной метрике"""
    global _top_posts_container, _metric_buttons
    
    # Проверяем наличие данных
    if not STATE.posts:
        if _top_posts_container:
            _top_posts_container.content = "<div style='color:#6b7280; padding: 20px; text-align: center;'>Нет данных для отображения</div>"
        return
    
    # Проверяем наличие контейнера - если его нет, пытаемся найти в DOM
    if not _top_posts_container:
        # Контейнер еще не инициализирован, пропускаем обновление
        print("Warning: Top posts container not initialized yet")
        return
    
    start_date = STATE.last_fetch_params.get("start_date", "")
    end_date = STATE.last_fetch_params.get("end_date", "")
    if not start_date or not end_date:
        if _top_posts_container:
            _top_posts_container.content = "<div style='color:#6b7280; padding: 20px; text-align: center;'>Период не выбран</div>"
        return
    
    try:
        # Фильтруем посты по периоду
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        selected_posts = [
            post for post in STATE.posts
            if start <= datetime.datetime.strptime(post['date'], "%Y-%m-%d").date() <= end
        ]
        
        # Убеждаемся, что ER рассчитан для всех постов (кешируем)
        for p in selected_posts:
            if '_er' not in p:
                views = p.get('views', 0)
                p['_er'] = calculate_er(
                    p.get('likes', 0),
                    p.get('comments', 0),
                    p.get('reposts', 0),
                    views
                )
        
        # Обновляем HTML с топ-постами
        html = format_top_posts(selected_posts, STATE.last_channel, mode)
        if _top_posts_container:
            try:
                _top_posts_container.content = html
            except Exception as e:
                print(f"Error updating top posts container: {e}")
        else:
            print("Warning: _top_posts_container is None")
        
        # Обновляем стили кнопок по аналогии с блоком "Саммари за период"
        # Активная кнопка - зеленый градиент (как карточка "Средний ER")
        # Неактивные кнопки - белый фон с серой обводкой (как остальные карточки)
        if _metric_buttons:
            for m, btn in _metric_buttons.items():
                try:
                    if m == mode:
                        # Активная кнопка: зеленый градиент, белый текст
                        btn.style('border: 1px solid #059669 !important; border-radius: 8px !important; background: linear-gradient(135deg, #059669 25%, #047857 100%) !important; color: #fff !important; font-size: 14px !important; font-weight: 500 !important; transition: all 0.2s !important; text-transform: none !important; box-shadow: none !important; padding: 8px 16px !important; min-width: fit-content !important;')
                    else:
                        # Неактивная кнопка: белый фон, серая обводка, темный текст
                        btn.style('border: 1px solid #e5e7eb !important; border-radius: 8px !important; background: #fff !important; color: #111827 !important; font-size: 14px !important; font-weight: 500 !important; transition: all 0.2s !important; text-transform: none !important; box-shadow: none !important; padding: 8px 16px !important; min-width: fit-content !important;')
                except Exception as e:
                    print(f"Error updating button style for {m}: {e}")
    except Exception as e:
        # В случае ошибки показываем сообщение
        print(f"Error in update_top_posts: {e}")
        import traceback
        traceback.print_exc()
        if _top_posts_container:
            try:
                _top_posts_container.content = f"<div style='color:#dc2626; padding: 20px; text-align: center;'>Ошибка при обновлении: {str(e)}</div>"
            except:
                pass


def render_top_posts():
    """Рендерит блок топ-постов"""
    global _metric_buttons, _top_posts_container
    
    # Сбрасываем глобальные переменные для чистого состояния
    _metric_buttons = {}
    _top_posts_container = None
    
    top_posts_card = ui.card().classes('w-full').style(
        'background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 32px; max-width: 1200px; display: none;'
    )
    
    with top_posts_card:
        ui.label('Топ-5 постов').classes('text-xl font-semibold mb-4').style('color: #111827;')
        ui.label('Выберите метрику для сортировки').classes('text-sm mb-4').style('color: #6b7280;')
        
        # Добавляем CSS стили для кнопок метрик только один раз
        global _css_styles_added
        if not _css_styles_added:
            ui.add_head_html('''
        <style>
            .metric-btn-custom {
                border: 1px solid #e5e7eb !important;
                border-radius: 8px !important;
                background: #fff !important;
                color: #111827 !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                transition: all 0.2s !important;
                text-transform: none !important;
                box-shadow: none !important;
                padding: 8px 16px !important;
                min-width: fit-content !important;
            }
            .metric-btn-custom.active {
                border: 1px solid #059669 !important;
                background: linear-gradient(135deg, #059669 25%, #047857 100%) !important;
                color: #fff !important;
            }
            .metric-btn-custom span,
            .metric-btn-custom .q-btn__content,
            .metric-btn-custom .q-btn__content > span {
                color: inherit !important;
                visibility: visible !important;
                opacity: 1 !important;
                display: inline-block !important;
            }
            .metric-btn-custom.active span,
            .metric-btn-custom.active .q-btn__content,
            .metric-btn-custom.active .q-btn__content > span {
                color: #fff !important;
            }
        </style>
        ''')
            _css_styles_added = True
        
        # Контейнер для кнопок переключения метрик
        metric_buttons_container = ui.row().classes('w-full gap-2 mb-4').style('flex-wrap: wrap;')
        
        # Создаем кнопки для каждой метрики
        metrics_config = [
            ('er', 'ER'),
            ('views', 'Просмотры'),
            ('likes', 'Лайки'),
            ('comments', 'Комментарии'),
            ('reposts', 'Репосты')
        ]
        
        for mode, label in metrics_config:
            with metric_buttons_container:
                # Используем ui.button - он автоматически отобразит label как текст
                btn = ui.button(label).classes('metric-btn-custom')
                if mode == 'er':
                    # По умолчанию ER активна - применяем стили активной кнопки сразу
                    btn.style('border: 1px solid #059669 !important; background: linear-gradient(135deg, #059669 25%, #047857 100%) !important; color: #fff !important;')
                _metric_buttons[mode] = btn
        
        # Контейнер для топ-постов - инициализируем с пустым содержимым
        _top_posts_container = ui.html('', sanitize=False).classes('w-full')
        
        # Привязываем обработчики кликов к кнопкам ВНУТРИ контекста карточки
        # Используем замыкание для правильного захвата значения
        for mode_key, btn in list(_metric_buttons.items()):
            # Создаем функцию-обертку для правильного захвата значения mode_key
            def make_handler(mode):
                def handler():
                    update_top_posts(mode)
                return handler
            btn.on('click', make_handler(mode_key))
        
        # Инициализируем отображение с метрикой по умолчанию (ER), если данные уже есть
        if STATE.posts and STATE.last_fetch_params:
            # Используем небольшую задержку, чтобы убедиться, что DOM готов
            def init_display():
                update_top_posts('er')
            ui.timer(0.2, init_display, once=True)
    
    return top_posts_card

