import os
from dotenv import load_dotenv
from nicegui import ui

# Импорты из новых модулей
from core.state import STATE
from ui.settings import render_settings
from ui.stats import render_stats
from ui.top_posts import render_top_posts
from ui.graphs import render_graphs
from ui.posting_insights import render_posting_insights
from ui.footer import render_footer

# ------------------ CONFIG LOADING ----------------------
def get_env_path():
    if '__file__' in globals():
        return os.path.join(os.path.dirname(__file__), 'idandhash.env')
    return os.path.join(os.getcwd(), 'idandhash.env')

load_dotenv(get_env_path())
API_ID = os.getenv('API_ID', '')
API_HASH = os.getenv('API_HASH', '')


# Стили в стиле других сайтов
ui.add_head_html('''
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background: #f9fafb; 
            color: #111827;
        }
        .plots-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            width: 100%;
        }
        @media (max-width: 768px) {
            .plots-grid {
                grid-template-columns: 1fr !important;
            }
        }
    </style>
''')

# STATE импортирован из core.state

# Инициализация UI
with ui.column().classes('w-full items-center gap-6').style('padding: 40px 20px; max-width: 1400px; margin: 0 auto;'):
    with ui.column().classes('w-full items-center mb-8'):
        ui.label('📊 Анализ Telegram-канала').classes('text-3xl font-bold').style('color: #111827; margin-bottom: 8px;')
    
    # Создаем компоненты в правильном порядке отображения
    # В NiceGUI порядок элементов в DOM определяется порядком их создания
    # Поэтому создаем settings первым, чтобы он отображался сверху
    
    # Сначала создаем скрытые карточки (они нужны для settings)
    stats_card, stats_container = render_stats()
    top_posts_card = render_top_posts()
    insights_card, insights_container = render_posting_insights()
    graphs_card = render_graphs()
    
    
    # Затем создаем settings (он будет первым в DOM и отобразится сверху)
    settings_card = render_settings(API_ID, API_HASH, stats_card, stats_container, graphs_card, top_posts_card, insights_card, insights_container)
    
    # Перемещаем settings_card в начало DOM с помощью JavaScript
    # Это нужно, чтобы settings всегда был сверху, даже если создается после других карточек
    ui.add_body_html('''
    <script>
        (function() {
            function moveSettingsToTop() {
                const container = document.querySelector('.w-full.items-center.gap-6');
                if (!container) return;
                
                // Находим все карточки
                const cards = Array.from(container.children);
                const settings = cards.find(c => {
                    const label = c.querySelector('.text-xl');
                    return label && label.textContent.trim() === 'Настройки';
                });
                
                if (settings) {
                    // Находим контейнер заголовка
                    const titleContainer = Array.from(container.children).find(c => 
                        c.querySelector('.text-3xl')
                    );
                    
                    if (titleContainer) {
                        // Перемещаем settings сразу после заголовка
                        if (titleContainer.nextSibling !== settings) {
                            container.insertBefore(settings, titleContainer.nextSibling);
                        }
                    } else {
                        // Если заголовка нет, перемещаем в начало
                        if (container.firstChild !== settings) {
                            container.insertBefore(settings, container.firstChild);
                        }
                    }
                }
            }
            
            // Пытаемся переместить после загрузки DOM
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', moveSettingsToTop);
            } else {
                setTimeout(moveSettingsToTop, 100);
            }
        })();
    </script>
    ''')
    
    # Footer в конце
    render_footer()

# Запуск приложения
# Примечание: index.html обслуживается веб-сервером (Nginx/Apache)
# который проксирует запросы к NiceGUI на этом порту
ui.run(title='Аналитика Телеграм-канала', host='0.0.0.0', port=80, reload=False)
