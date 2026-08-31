import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window

# Устанавливаем тёмный фоновый цвет приложения
Window.clearcolor = (0.12, 0.12, 0.12, 1)

class MessengerLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=15, spacing=10, **kwargs)
        
        self.api_url = ""
        self.username = ""
        self.token = ""

        # --- ЭКРАН 1: АВТОРИЗАЦИЯ ---
        self.title_label = Label(
            text="[b]GitHub Messenger[/b]", 
            markup=True, 
            font_size='24sp', 
            size_hint_y=None, 
            height=50
        )
        
        self.nickname_input = TextInput(
            hint_text="Ваш никнейм...", 
            multiline=False, 
            size_hint_y=None, 
            height=50
        )
        
        self.url_input = TextInput(
            hint_text="URL API (https://api.github.com/...)", 
            multiline=False, 
            size_hint_y=None, 
            height=50
        )
        
        self.token_input = TextInput(
            hint_text="GitHub Token (необязательно, для отправки)", 
            password=True, 
            multiline=False, 
            size_hint_y=None, 
            height=50
        )
        
        self.login_btn = Button(
            text="Войти в чат", 
            size_hint_y=None, 
            height=55, 
            background_color=(0.2, 0.6, 1, 1)
        )
        self.login_btn.bind(on_press=self.login)

        # Добавляем виджеты входа на экран
        self.add_widget(self.title_label)
        self.add_widget(self.nickname_input)
        self.add_widget(self.url_input)
        self.add_widget(self.token_input)
        self.add_widget(self.login_btn)

    def login(self, instance):
        nick = self.nickname_input.text.strip()
        url = self.url_input.text.strip()
        
        if not nick or not url:
            return

        self.username = nick
        self.api_url = url
        self.token = self.token_input.text.strip()

        # Очищаем экран авторизации и строим интерфес чата
        self.clear_widgets()

        # --- ЭКРАН 2: ОКТИВНЫЙ ЧАТ ---
        self.scroll = ScrollView(size_hint=(1, 1))
        
        self.messages_label = Label(
            text="Подключение к GitHub...\n", 
            markup=True, 
            size_hint_y=None, 
            font_size='16sp',
            halign='left',
            valign='top'
        )
        self.messages_label.bind(
            texture_size=lambda inst, val: setattr(inst, 'height', val[1])
        )
        self.messages_label.bind(
            width=lambda inst, val: setattr(inst, 'text_size', (val, None))
        )
        self.scroll.add_widget(self.messages_label)

        # Поле ввода и кнопка
        self.msg_input = TextInput(
            hint_text="Сообщение...", 
            multiline=False, 
            size_hint_x=0.75
        )
        self.send_btn = Button(
            text="Отправить", 
            size_hint_x=0.25, 
            background_color=(0.2, 0.8, 0.4, 1)
        )
        self.send_btn.bind(on_press=self.send_message)

        input_box = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=50, 
            spacing=5
        )
        input_box.add_widget(self.msg_input)
        input_box.add_widget(self.send_btn)

        self.add_widget(self.scroll)
        self.add_widget(input_box)

        # Первичная загрузка и запуск автообновления каждые 3 секунды
        self.fetch_messages(0)
        Clock.schedule_interval(self.fetch_messages, 3)

    def fetch_messages(self, dt):
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"token {self.token}"

            res = requests.get(self.api_url, headers=headers, timeout=5)
            if res.status_code == 200:
                comments = res.json()
                chat_text = ""
                for c in comments:
                    body = c.get('body', '')
                    chat_text += f"{body}\n\n"
                
                if not chat_text:
                    chat_text = "[color=888888]Сообщений пока нет... Напишите первым![/color]"
                    
                self.messages_label.text = chat_text
            else:
                self.messages_label.text = f"[color=ff4444]Ошибка сервера: {res.status_code}[/color]"
        except Exception as e:
            self.messages_label.text = f"[color=ff4444]Ошибка соединения с GitHub[/color]"

    def send_message(self, instance):
        text = self.msg_input.text.strip()
        if not text:
            return

        formatted_msg = f"[color=3388ff][b]{self.username}[/b]:[/color] {text}"

        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        try:
            res = requests.post(
                self.api_url, 
                json={"body": formatted_msg}, 
                headers=headers, 
                timeout=5
            )
            if res.status_code in [200, 201]:
                self.msg_input.text = ""
                self.fetch_messages(0)
            else:
                print(f"Ошибка отправки: {res.status_code}")
        except Exception as e:
            print(f"Исключение при отправке: {e}")


class GitMessengerApp(App):
    def build(self):
        self.title = "GitHub Messenger"
        return MessengerLayout()

if __name__ == '__main__':
    GitMessengerApp().run()
