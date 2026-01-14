"""
Модуль для работы с Яндекс.Метрикой
Предоставляет безопасный API для отправки событий и параметров
"""
import json
from typing import Optional, Dict, Any


# ID счетчика Яндекс.Метрики
METRIKA_ID = 106259012

# Флаг инициализации глобальной функции
_metrika_helper_initialized = False


def _ensure_helper_initialized():
    """Инициализирует глобальную JavaScript функцию для работы с Метрикой"""
    global _metrika_helper_initialized
    if _metrika_helper_initialized:
        return
    
    from nicegui import ui
    
    # Создаем глобальную функцию для отправки событий
    helper_script = f"""
    (function() {{
        window._ymTrack = function(eventName, params) {{
            if (window.ym) {{
                try {{
                    if (params && Object.keys(params).length > 0) {{
                        window.ym({METRIKA_ID}, 'reachGoal', eventName, params);
                    }} else {{
                        window.ym({METRIKA_ID}, 'reachGoal', eventName);
                    }}
                    console.log('Yandex Metrika: tracked event', eventName, params || '');
                }} catch(e) {{
                    console.warn('Yandex Metrika error:', e);
                }}
            }} else {{
                console.warn('Yandex Metrika: window.ym not available');
            }}
        }};
        
        window._ymSetParams = function(params) {{
            if (window.ym) {{
                try {{
                    window.ym({METRIKA_ID}, 'params', params);
                    console.log('Yandex Metrika: set params', params);
                }} catch(e) {{
                    console.warn('Yandex Metrika error:', e);
                }}
            }} else {{
                console.warn('Yandex Metrika: window.ym not available');
            }}
        }};
    }})();
    """
    
    ui.add_body_html(f'<script>{helper_script}</script>')
    _metrika_helper_initialized = True


def track(event_name: str, payload: Optional[Dict[str, Any]] = None) -> None:
    """
    Безопасно отправляет событие в Яндекс.Метрику.
    
    Args:
        event_name: Название события (goal)
        payload: Опциональные параметры события
    
    Примеры:
        track('get_statistics')
        track('change_period', {'period_start': '2024-01-01', 'period_end': '2024-01-31'})
    """
    try:
        _ensure_helper_initialized()
        from nicegui import ui
        
        # Используем JSON для безопасной передачи параметров
        if payload:
            params_json = json.dumps(payload, ensure_ascii=False)
            # Используем более надежный способ вызова с проверкой доступности функции
            js_code = f"""
            (function() {{
                if (typeof window._ymTrack === 'function') {{
                    window._ymTrack({json.dumps(event_name)}, {params_json});
                }} else {{
                    // Если функция еще не загружена, ждем и пробуем снова
                    setTimeout(function() {{
                        if (typeof window._ymTrack === 'function') {{
                            window._ymTrack({json.dumps(event_name)}, {params_json});
                        }} else {{
                            console.warn('Yandex Metrika: _ymTrack function not available');
                        }}
                    }}, 100);
                }}
            }})();
            """
        else:
            js_code = f"""
            (function() {{
                if (typeof window._ymTrack === 'function') {{
                    window._ymTrack({json.dumps(event_name)});
                }} else {{
                    setTimeout(function() {{
                        if (typeof window._ymTrack === 'function') {{
                            window._ymTrack({json.dumps(event_name)});
                        }} else {{
                            console.warn('Yandex Metrika: _ymTrack function not available');
                        }}
                    }}, 100);
                }}
            }})();
            """
        
        # Выполняем JavaScript код
        ui.run_javascript(js_code)
    except Exception as e:
        # Логируем ошибку для отладки, но не прерываем работу приложения
        print(f"Yandex Metrika track error: {e}")
        pass


def set_params(params: Dict[str, Any]) -> None:
    """
    Устанавливает пользовательские параметры в Яндекс.Метрике.
    
    Args:
        params: Словарь с параметрами (например, {'user_type': 'guest', 'source': 'direct'})
    
    Пример:
        set_params({'user_type': 'guest', 'source': 'direct'})
    """
    try:
        _ensure_helper_initialized()
        from nicegui import ui
        
        params_json = json.dumps(params, ensure_ascii=False)
        js_code = f"""
        (function() {{
            if (typeof window._ymSetParams === 'function') {{
                window._ymSetParams({params_json});
            }} else {{
                setTimeout(function() {{
                    if (typeof window._ymSetParams === 'function') {{
                        window._ymSetParams({params_json});
                    }} else {{
                        console.warn('Yandex Metrika: _ymSetParams function not available');
                    }}
                }}, 100);
            }}
        }})();
        """
        
        ui.run_javascript(js_code)
    except Exception as e:
        print(f"Yandex Metrika set_params error: {e}")
        pass


