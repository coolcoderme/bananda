from bananda import App, BoxLayout, Button, Label, TextInput


class TreeApp(App):
    title = "Tree"

    def build(self):
        root = BoxLayout(orientation="vertical", padding=8, spacing=4)
        root.add_widget(Label(text="Hello"))
        btn = Button(text="Go")
        btn.bind(on_press=self.clicked)
        root.add_widget(btn)
        return root

    def clicked(self, instance):
        instance.text = "Gone"


def test_widget_tree_and_events():
    app = TreeApp()
    root = app.build()
    assert len(root.children) == 2
    assert root.children[0].text == "Hello"
    button = root.children[1]
    assert button.text == "Go"
    button.dispatch("on_press")
    assert button.text == "Gone"
    dumped = root.dump()
    assert "BoxLayout" in dumped
    assert "Label(text='Hello')" in dumped


def test_walk_and_clear():
    root = BoxLayout()
    root.add_widget(Label(text="a"))
    root.add_widget(Label(text="b"))
    assert len(root.walk()) == 3
    root.clear_widgets()
    assert root.children == []


def test_textinput_dispatch():
    seen = []
    field = TextInput(hint_text="name")
    field.bind(on_text=lambda inst, value: seen.append(value))
    field.dispatch("on_text", "Ada")
    assert seen == ["Ada"]
