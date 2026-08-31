import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.uix.popup import Popup
from kivy.core.clipboard import Clipboard


class MessengerLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 15
        self.spacing = 10

        self.store = JsonStore("messenger_config.json")
        self.repo_owner = "333saif666-cyber"
        self.repo_name = "messendger"
        self.current_issue_id = "1"

        saved_nickname = (
            self.store.get("user")["nickname"]
            if self.store.exists("user")
            else "333saif666-cyber"
        )
        saved_token = (
            self.store.get("user")["token"]
            if self.store.exists("user")
            else ""
        )

        # --- ЦЕНТРИРОВАННЫЙ ЭКРАН ВХОДА ---
        self.login_wrapper = BoxLayout(orientation="vertical")

        self.login_box = BoxLayout(
            orientation="vertical",
            spacing=10,
            size_hint=(0.9, None),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.login_box.bind(minimum_height=self.login_box.setter("height"))

        self.login_box.add_widget(
            Label(
                text="GitHub Messenger",
                font_size=24,
                bold=True,
                size_hint_y=None,
                height=45,
            )
        )

        # Поле Никнейма
        self.nickname_input = TextInput(
            text=saved_nickname,
            hint_text="Ваш никнейм...",
            multiline=False,
            size_hint_y=None,
            height=45,
        )
        self.login_box.add_widget(self.nickname_input)

        # Поле Токена с кнопкой «Вставить из буфера»
        token_row = BoxLayout(
            orientation="horizontal",
            spacing=5,
            size_hint_y=None,
            height=45,
        )
        self.token_input = TextInput(
            text=saved_token,
            hint_text="GitHub Token (ghp_...)",
            multiline=False,
            password=True,
        )
        paste_token_btn = Button(text="Вставить", size_hint_x=0.3)
        paste_token_btn.bind(
            on_press=lambda inst: setattr(
                self.token_input, "text", Clipboard.paste()
            )
        )

        token_row.add_widget(self.token_input)
        token_row.add_widget(paste_token_btn)
        self.login_box.add_widget(token_row)

        self.login_btn = Button(
            text="Сохранить и войти",
            size_hint_y=None,
            height=50,
            background_color=(0.1, 0.4, 0.8, 1),
        )
        self.login_btn.bind(on_press=self.enter_chat)
        self.login_box.add_widget(self.login_btn)

        # Центрирование через пустышки сверху и снизу
        self.login_wrapper.add_widget(BoxLayout())
        self.login_wrapper.add_widget(self.login_box)
        self.login_wrapper.add_widget(BoxLayout())

        self.add_widget(self.login_wrapper)

        # --- ЭКРАН ЧАТА ---
        self.chat_box = BoxLayout(orientation="vertical", spacing=8)

        # Верхняя панель управления
        self.top_bar = BoxLayout(
            orientation="horizontal", spacing=5, size_hint_y=None, height=40
        )
        self.new_chat_btn = Button(text="+ Новый чат", size_hint_x=0.5)
        self.new_chat_btn.bind(on_press=self.show_create_chat_popup)

        self.add_user_btn = Button(text="+ Юзер", size_hint_x=0.5)
        self.add_user_btn.bind(on_press=self.show_add_user_popup)

        self.top_bar.add_widget(self.new_chat_btn)
        self.top_bar.add_widget(self.add_user_btn)

        # Сообщения
        self.messages_label = Label(
            text="Загрузка...",
            size_hint_y=None,
            halign="left",
            valign="top",
            markup=True,
        )
        self.messages_label.bind(
            texture_size=lambda instance, value: setattr(
                instance, "height", value[1]
            )
        )
        self.messages_label.bind(
            width=lambda instance, value: setattr(
                instance, "text_size", (value, None)
            )
        )

        self.scroll_view = ScrollView()
        self.scroll_view.add_widget(self.messages_label)

        # Панель ввода сообщения с буфером обмена
        self.input_box = BoxLayout(
            orientation="horizontal",
            spacing=5,
            size_hint_y=None,
            height=50,
        )
        self.message_input = TextInput(
            hint_text="Сообщение...", multiline=False
        )

        paste_msg_btn = Button(text="📋", size_hint_x=0.15)
        paste_msg_btn.bind(
            on_press=lambda inst: setattr(
                self.message_input,
                "text",
                self.message_input.text + Clipboard.paste(),
            )
        )

        self.send_btn = Button(text="Отправить", size_hint_x=0.25)
        self.send_btn.bind(on_press=self.send_message)

        self.input_box.add_widget(self.message_input)
        self.input_box.add_widget(paste_msg_btn)
        self.input_box.add_widget(self.send_btn)

        self.chat_box.add_widget(self.top_bar)
        self.chat_box.add_widget(self.scroll_view)
        self.chat_box.add_widget(self.input_box)

        # Автоматический вход, если токен уже есть
        if saved_token:
            Clock.schedule_once(lambda dt: self.enter_chat(None), 0.5)

    def enter_chat(self, instance):
        self.token = self.token_input.text.strip()
        self.nickname = self.nickname_input.text.strip()

        if not self.token:
            return

        self.store.put("user", nickname=self.nickname, token=self.token)

        self.clear_widgets()
        self.add_widget(self.chat_box)

        self.load_messages()
        Clock.schedule_interval(self.load_messages, 3)

    def load_messages(self, *args):
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{self.current_issue_id}/comments"
        headers = (
            {"Authorization": f"token {self.token}"} if self.token else {}
        )

        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                comments = res.json()
                chat_text = ""
                for comment in comments:
                    user = comment.get("user", {}).get("login", "Unknown")
                    body = comment.get("body", "")
                    chat_text += f"[b]{user}:[/b] {body}\n\n"

                self.messages_label.text = chat_text or "Чат пуст."
        except Exception:
            pass

    def send_message(self, instance):
        text = self.message_input.text.strip()
        if not text or not self.token:
            return

        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{self.current_issue_id}/comments"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            res = requests.post(
                url, json={"body": text}, headers=headers, timeout=5
            )
            if res.status_code in [200, 201]:
                self.message_input.text = ""
                self.load_messages()
        except Exception:
            pass

    def show_create_chat_popup(self, instance):
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        chat_name_input = TextInput(
            hint_text="Название чата...", multiline=False
        )
        create_btn = Button(text="Создать", size_hint_y=None, height=45)

        content.add_widget(chat_name_input)
        content.add_widget(create_btn)

        popup = Popup(
            title="Создать новый чат", content=content, size_hint=(0.85, 0.35)
        )

        def create_chat(btn_instance):
            title = chat_name_input.text.strip()
            if not title:
                return

            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues"
            headers = {"Authorization": f"token {self.token}"}
            res = requests.post(url, json={"title": title}, headers=headers)

            if res.status_code == 201:
                issue_data = res.json()
                self.current_issue_id = str(issue_data["number"])
                popup.dismiss()
                self.load_messages()

        create_btn.bind(on_press=create_chat)
        popup.open()

    def show_add_user_popup(self, instance):
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        user_input = TextInput(
            hint_text="Никнейм на GitHub...", multiline=False
        )

        paste_user_btn = Button(text="Вставить ник из буфера", size_hint_y=None, height=35)
        paste_user_btn.bind(
            on_press=lambda inst: setattr(
                user_input, "text", Clipboard.paste()
            )
        )

        add_btn = Button(text="Пригласить", size_hint_y=None, height=45)

        content.add_widget(user_input)
        content.add_widget(paste_user_btn)
        content.add_widget(add_btn)

        popup = Popup(
            title="Пригласить пользователя",
            content=content,
            size_hint=(0.85, 0.45),
        )

        def add_user(btn_instance):
            target_user = user_input.text.strip()
            if target_user:
                url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{self.current_issue_id}/comments"
                headers = {"Authorization": f"token {self.token}"}
                requests.post(
                    url,
                    json={
                        "body": f"👋 Привет, @{target_user}! Тебя добавили в этот чат."
                    },
                    headers=headers,
                )
                popup.dismiss()
                self.load_messages()

        add_btn.bind(on_press=add_user)
        popup.open()


class GitMessengerApp(App):
    def build(self):
        return MessengerLayout()


if __name__ == "__main__":
    GitMessengerApp().run()
