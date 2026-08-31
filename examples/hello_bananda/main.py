"""BanANDa test application: a counter and greeting demo.

This file is ordinary Python that uses the BanANDa widget API. ``bananda build``
converts it to Kotlin and packages a native APK — the Android app does not
embed a Python interpreter.
"""

from bananda import App, BoxLayout, Button, Label, TextInput


class DemoApp(App):
    title = "BanANDa Demo"

    def build(self):
        self.count = 0
        self.name = ""

        root = BoxLayout(orientation="vertical", padding=24, spacing=16)

        root.add_widget(Label(text="BanANDa", font_size=32, color="#5D4A00", bold=True))
        root.add_widget(
            Label(
                text="Python to Kotlin, no interpreter",
                font_size=14,
                color="#7A6A33",
            )
        )

        self.counter_label = Label(text="Count: 0", font_size=28, color="#1A1A1A")
        root.add_widget(self.counter_label)

        row = BoxLayout(
            orientation="horizontal",
            spacing=12,
            size_hint=(1, None),
            height=56,
        )
        row.add_widget(Button(text="+1", on_press=self.increment))
        row.add_widget(Button(text="-1", on_press=self.decrement))
        row.add_widget(Button(text="Reset", on_press=self.reset))
        root.add_widget(row)

        root.add_widget(Label(text="Your name", font_size=16, color="#5D4A00"))
        self.name_input = TextInput(hint_text="Type here", on_text=self.on_name)
        root.add_widget(self.name_input)

        root.add_widget(Button(text="Greet me", on_press=self.greet))
        self.greeting = Label(text="Hello, friend!", font_size=20, color="#3D2E00")
        root.add_widget(self.greeting)
        return root

    def increment(self, instance):
        self.count = self.count + 1
        self._refresh_counter()

    def decrement(self, instance):
        self.count = self.count - 1
        self._refresh_counter()

    def reset(self, instance):
        self.count = 0
        self._refresh_counter()

    def _refresh_counter(self):
        self.counter_label.text = f"Count: {self.count}"

    def on_name(self, instance, value):
        self.name = value

    def greet(self, instance):
        who = self.name.strip()
        if not who:
            who = "friend"
        self.greeting.text = f"Hello, {who}! Count is {self.count}."


if __name__ == "__main__":
    DemoApp().run()
