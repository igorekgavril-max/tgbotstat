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
    
    <!-- Yandex.Metrika counter -->
    <script type="text/javascript">
        (function(m,e,t,r,i,k,a){
            m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
            m[i].l=1*new Date();
            for (var j = 0; j < document.scripts.length; j++) {
                if (document.scripts[j].src === r) { return; }
            }
            k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
        })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=106259012', 'ym');

        // Инициализация Метрики после загрузки скрипта
        (function() {
            function initMetrika() {
                if (window.ym) {
                    try {
                        window.ym(106259012, 'init', {
                            ssr: true,
                            webvisor: true,
                            clickmap: true,
                            ecommerce: "dataLayer",
                            accurateTrackBounce: true,
                            trackLinks: true
                        });
                        console.log('Yandex Metrika initialized');
                    } catch(e) {
                        console.warn('Yandex Metrika init error:', e);
                    }
                }
            }
            
            // Пытаемся инициализировать сразу, если ym уже доступен
            if (window.ym && typeof window.ym === 'function') {
                initMetrika();
            } else {
                // Ждем загрузки скрипта
                var checkInterval = setInterval(function() {
                    if (window.ym && typeof window.ym === 'function') {
                        clearInterval(checkInterval);
                        initMetrika();
                    }
                }, 50);
                
                // Таймаут на случай, если скрипт не загрузится
                setTimeout(function() {
                    clearInterval(checkInterval);
                    if (!window.ym) {
                        console.warn('Yandex Metrika: script failed to load');
                    }
                }, 5000);
            }
        })();
        
        // Глобальная функция для отправки событий (инициализируется сразу)
        (function() {
            window._ymTrack = function(eventName, params) {
                if (window.ym && typeof window.ym === 'function') {
                    try {
                        if (params && Object.keys(params).length > 0) {
                            window.ym(106259012, 'reachGoal', eventName, params);
                        } else {
                            window.ym(106259012, 'reachGoal', eventName);
                        }
                        console.log('Yandex Metrika: tracked event', eventName, params || '');
                    } catch(e) {
                        console.warn('Yandex Metrika error:', e);
                    }
                } else {
                    console.warn('Yandex Metrika: window.ym not available');
                }
            };
            
            window._ymSetParams = function(params) {
                if (window.ym && typeof window.ym === 'function') {
                    try {
                        window.ym(106259012, 'params', params);
                        console.log('Yandex Metrika: set params', params);
                    } catch(e) {
                        console.warn('Yandex Metrika error:', e);
                    }
                } else {
                    console.warn('Yandex Metrika: window.ym not available');
                }
            };
        })();
    </script>

    <noscript>
        <div>
            <img src="https://mc.yandex.ru/watch/106259012"
                 style="position:absolute; left:-9999px;" alt="" />
        </div>
    </noscript>
    <!-- /Yandex.Metrika counter -->
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
ui.run(title='Аналитика Телеграм-канала', host='127.0.0.1', port=8000, reload=False)
