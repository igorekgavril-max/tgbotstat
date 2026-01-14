"""
UI компонент: Блок настроек
"""
import datetime
from nicegui import ui
from core.state import STATE
from core.services import fetch_posts_async, extract_channel_username
from core.analytics import calculate_previous_period, compare_periods, calculate_er
from core.request_logger import log_statistics_request
from core.yandex_metrika import track
from ui.stats import stats_html
from ui.top_posts import update_top_posts
from ui.posting_insights import update_posting_insights


def is_valid_date(date_str: str) -> bool:
    """Проверяет валидность даты"""
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except Exception:
        return False


def render_settings(
    api_id: str,
    api_hash: str,
    stats_card,
    stats_container,
    graphs_card,
    top_posts_card,
    insights_card,
    insights_container
):
    """
    Рендерит блок настроек
    
    Args:
        api_id: API ID Telegram
        api_hash: API Hash Telegram
        stats_card: Карточка статистики
        stats_container: Контейнер для HTML статистики
        graphs_card: Карточка графиков
        top_posts_card: Карточка топ-постов
        insights_card: Карточка инсайтов о времени публикаций
        insights_container: Контейнер для HTML инсайтов
    """
    settings_card = ui.card().classes('w-full').style(
        'background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 32px; max-width: 800px;'
    )
    
    with settings_card:
        ui.label('Настройки').classes('text-xl font-semibold mb-6').style('color: #111827;')
        
        channel_input = ui.input('Ссылка на канал', value='@tech_igor').classes('w-full mb-4').style('font-size: 18px;')
        
        with ui.row().classes('w-full gap-4'):
            date_from = ui.input(
                label='Дата от (YYYY-MM-DD)',
                value=(datetime.date.today().replace(year=datetime.date.today().year - 1)).strftime('%Y-%m-%d')
            ).classes('flex-1').style('font-size: 18px;')
            date_to = ui.input(
                label='Дата до (YYYY-MM-DD)',
                value=datetime.date.today().strftime('%Y-%m-%d')
            ).classes('flex-1').style('font-size: 18px;')
        
        compare_switch = ui.switch('Сравнить с предыдущим периодом', value=False).classes('w-full mt-2').style('font-size: 16px;')
        
        fetch_button = ui.button('Получить статистику', color='primary').classes('w-full mt-2').style(
            'background: #111827; color: #fff; font-weight: 600; padding: 12px 24px; border-radius: 8px; font-size: 20px;'
        )
        progress_label = ui.label('').classes('mt-4').style('color: #059669; font-size: 14px; font-weight: 500;')
            
        def auto_reset_stats():
            """Сбрасывает статистику при изменении параметров"""
            STATE.reset()
            
            if stats_container:
                stats_container.content = ""
            
            progress_label.text = ""
            
            # Скрываем блоки статистики и графиков при изменении параметров
            if stats_card:
                stats_card.style('display: none;')
            if graphs_card:
                graphs_card.style('display: none;')
            if top_posts_card:
                top_posts_card.style('display: none;')
            if insights_card:
                insights_card.style('display: none;')

        def on_date_change():
            """Обработчик изменения дат - отслеживает событие change_period"""
            d_from = date_from.value.strip()
            d_to = date_to.value.strip()
            
            # Отслеживаем изменение периода только если даты валидны
            if d_from and d_to and is_valid_date(d_from) and is_valid_date(d_to) and d_from <= d_to:
                track('change_period', {
                    'period_start': d_from,
                    'period_end': d_to
                })
            
            auto_reset_stats()

        channel_input.on('change', lambda _: auto_reset_stats())
        date_from.on('change', lambda _: on_date_change())
        date_to.on('change', lambda _: on_date_change())
        compare_switch.on('change', lambda _: auto_reset_stats())
    
        async def on_fetch():
            """Обработчик кнопки получения статистики"""
            channel = channel_input.value.strip()
            d_from = date_from.value.strip()
            d_to = date_to.value.strip()
            compare = compare_switch.value
            
            if not channel or not d_from or not d_to:
                progress_label.text = "⛔ Пожалуйста, заполните все поля"
                return

            if not is_valid_date(d_from) or not is_valid_date(d_to):
                progress_label.text = "⛔ Проверьте формат дат (YYYY-MM-DD)"
                return

            if d_from > d_to:
                progress_label.text = "⛔ Дата 'от' не должна быть позже даты 'до'"
                return

            # Проверяем, является ли это повторной загрузкой для того же периода
            is_refresh = (
                STATE.last_fetch_params and
                STATE.last_fetch_params.get('start_date') == d_from and
                STATE.last_fetch_params.get('end_date') == d_to and
                STATE.last_channel == channel
            )
            
            # Отслеживаем события Яндекс.Метрики
            if is_refresh:
                # Повторная загрузка для того же периода
                track('refresh_statistics')
            else:
                # Первая загрузка или новый период
                track('get_statistics')

            # Логируем запрос ДО начала загрузки данных
            # Это гарантирует, что запрос будет залогирован даже при ошибке загрузки
            # Используем канал как логин (извлекаем username из ссылки)
            channel_login = extract_channel_username(channel)
            log_statistics_request(start_date=d_from, end_date=d_to, login=channel_login)

            fetch_button.disable()
            progress_label.text = "⏳ Получение постов..."
            
            async def progress_cb(msg):
                progress_label.text = msg
            
            try:
                # Загружаем данные основного периода
                STATE.posts = await fetch_posts_async(api_id, api_hash, channel, d_from, d_to, limit=1500, progress_callback=progress_cb)
                STATE.last_fetch_params = {"start_date": d_from, "end_date": d_to}
                STATE.last_channel = channel
                STATE.compare_enabled = compare
                STATE.start_date = d_from
                STATE.end_date = d_to
                STATE.channel = channel
                
                comparison_data = None
                
                # Если включено сравнение, загружаем данные предыдущего периода
                if compare:
                    prev_start, prev_end = calculate_previous_period(d_from, d_to)
                    progress_label.text = f"⏳ Загрузка предыдущего периода ({prev_start} — {prev_end})..."
                    STATE.previous_posts = await fetch_posts_async(
                        api_id, api_hash, channel, prev_start, prev_end, limit=1500, progress_callback=None
                    )
                    
                    # Фильтруем посты по периодам
                    start = datetime.datetime.strptime(d_from, "%Y-%m-%d").date()
                    end = datetime.datetime.strptime(d_to, "%Y-%m-%d").date()
                    prev_start_dt = datetime.datetime.strptime(prev_start, "%Y-%m-%d").date()
                    prev_end_dt = datetime.datetime.strptime(prev_end, "%Y-%m-%d").date()
                    
                    current_posts = [
                        post for post in STATE.posts
                        if start <= datetime.datetime.strptime(post['date'], "%Y-%m-%d").date() <= end
                    ]
                    previous_posts = [
                        post for post in STATE.previous_posts
                        if prev_start_dt <= datetime.datetime.strptime(post['date'], "%Y-%m-%d").date() <= prev_end_dt
                    ]
                    
                    comparison_data = compare_periods(current_posts, previous_posts)
                    progress_label.text = f"✅ Получено {len(current_posts)} постов (текущий) и {len(previous_posts)} постов (предыдущий)"
                else:
                    STATE.previous_posts = []
                    progress_label.text = f"✅ Получено {len(STATE.posts)} постов"
                
                html = stats_html(STATE.posts, d_from, d_to, channel, comparison_data)
                stats_container.content = html
                # Показываем блоки статистики и графиков
                stats_card.style('display: block;')
                graphs_card.style('display: block;')
                top_posts_card.style('display: block;')
                insights_card.style('display: block;')
                # Обновляем инсайты о времени публикаций
                update_posting_insights(insights_container)
                # Обновляем топ-посты с метрикой по умолчанию (ER) после небольшой задержки
                # чтобы гарантировать, что контейнер полностью инициализирован в DOM
                def update_top_posts_delayed():
                    update_top_posts('er')
                ui.timer(0.1, update_top_posts_delayed, once=True)
            except Exception as e:
                STATE.reset()
                progress_label.text = f"⛔ Ошибка: {str(e)}"
                stats_container.content = ""
                # Скрываем блоки при ошибке
                stats_card.style('display: none;')
                graphs_card.style('display: none;')
                top_posts_card.style('display: none;')
                insights_card.style('display: none;')
            finally:
                fetch_button.enable()

        fetch_button.on('click', on_fetch)
    
    return settings_card

