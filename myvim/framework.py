# myvim/framework.py
import curses
from abc import ABC, abstractmethod

# --- БАЗОВЫЕ КОМПОНЕНТЫ MVC ---

class BaseModel:
    """Базовый класс для любой Модели."""
    def __init__(self):
        self.message = ""

class BaseView(ABC):
    """Базовый класс для любого Представления."""
    @abstractmethod
    def render(self, model, *args, **kwargs):
        pass

class BaseController(ABC):
    """Базовый класс для любого Контроллера."""
    @abstractmethod
    def run(self):
        pass

# --- ПАТТЕРН "СТРОИТЕЛЬ" (BUILDER) ---

class TuiAppBuilder:
    """
    Строитель приложения (Паттерн Builder).
    Позволяет пошагово сконфигурировать приложение и собрать его.
    """
    def __init__(self):
        # ИСПРАВЛЕНО: правильная инициализация всех полей
        self._model = None
        self._view_class = None
        self._view_args = ()
        self._view_kwargs = {}
        self._controller_class = None
        self._controller_kwargs = {}

    def set_model(self, model: BaseModel):
        self._model = model
        return self

    def set_view(self, view_class, *args, **kwargs):
        # Передаем класс, так как View требует адаптер curses, который появится позже
        self._view_class = view_class
        self._view_args = args
        self._view_kwargs = kwargs
        return self

    def set_controller(self, controller_class, **kwargs):
        self._controller_class = controller_class
        self._controller_kwargs = kwargs
        return self

    def build(self):
        """Собирает и возвращает готовое приложение."""
        # ИСПРАВЛЕНО: используем self._model вместо self.model
        if not self._model or not self._view_class or not self._controller_class:
            raise ValueError("Builder: Model, View and Controller must be set!")
        
        return TuiApplication(
            self._model, self._view_class, self._view_args, self._view_kwargs,
            self._controller_class, self._controller_kwargs
        )

# --- ЯДРО ПРИЛОЖЕНИЯ (ИНИЦИАЛИЗАЦИЯ CURSES) ---

class TuiApplication:
    def __init__(self, model, view_class, view_args, view_kwargs, controller_class, controller_kwargs):
        self.model = model
        self.view_class = view_class
        self.view_args = view_args
        self.view_kwargs = view_kwargs
        self.controller_class = controller_class
        self.controller_kwargs = controller_kwargs

    def run(self):
        """Запускает curses-цикл."""
        def _main(stdscr):
            # Инициализация адаптера curses
            from .curses_adapter import CursesAdapter
            adapter = CursesAdapter(stdscr)

            # Создаем View (передаем туда адаптер)
            view = self.view_class(adapter, *self.view_args, **self.view_kwargs)

            # Создаем Controller (передаем модель, view и другие аргументы)
            controller = self.controller_class(
                model=self.model, 
                view=view, 
                input_source=adapter,
                **self.controller_kwargs
            )

            # Запуск главного цикла
            controller.run()

        curses.wrapper(_main)