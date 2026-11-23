from .framework import BaseModel, BaseView, BaseController, TuiAppBuilder
import curses

# --- ДЕМО-МОДЕЛЬ ---
class CounterModel(BaseModel):
    def __init__(self):
        super().__init__()
        self.count = 0

    def increment(self):
        self.count += 1

    def decrement(self):
        self.count -= 1

# --- ДЕМО-ПРЕДСТАВЛЕНИЕ ---
class CounterView(BaseView):
    def __init__(self, target):
        self.target = target

    def render(self, model, mode_name="", message=""):
        t = self.target
        t.clear()
        h, w = t.getmaxyx()
        
        # Рисуем заголовок
        t.addstr(1, 2, "--- Demo App: Simple Counter ---", curses.A_BOLD)
        t.addstr(3, 2, f"Current Count: {model.count}", curses.color_pair(4))
        t.addstr(5, 2, "Controls: [ + ] increment, [ - ] decrement, [ q ] quit")
        
        if message:
            t.addstr(7, 2, f"Msg: {message}", curses.color_pair(3))
            
        t.refresh()

# --- ДЕМО-КОНТРОЛЛЕР ---
class CounterController(BaseController):
    def __init__(self, model, view, input_source):
        self.model = model
        self.view = view
        self.input = input_source
        self.running = True

    def run(self):
        while self.running:
            self.view.render(self.model, message=self.model.message)
            self.model.message = "" # Очищаем сообщение
            
            key = self.input.get_key()
            if key == -1: break
            ch = chr(key) if 0 <= key <= 255 else ""

            if ch == 'q':
                self.running = False
            elif ch == '+':
                self.model.increment()
                self.model.message = "Incremented!"
            elif ch == '-':
                self.model.decrement()
                self.model.message = "Decremented!"

# --- ТОЧКА ВХОДА ДЕМО ---
def run_demo():
    model = CounterModel()
    builder = TuiAppBuilder()
    app = (builder
           .set_model(model)
           .set_view(CounterView)
           .set_controller(CounterController)
           .build())
    app.run()

if __name__ == "__main__":
    run_demo()