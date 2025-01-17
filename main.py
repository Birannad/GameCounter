import json
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Rectangle, Color
from kivy.core.window import Window

# --------------------------
# Game Class
# --------------------------
class Game:
    def __init__(self, name, timestamp=None, players=None):
        self.name = name
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.players = players or {}

    def add_player(self, player_name):
        if player_name in self.players:
            raise ValueError(f"Player '{player_name}' already exists.")
        self.players[player_name] = 0

    def remove_player(self, player_name):
        if player_name in self.players:
            del self.players[player_name]

    def update_score(self, player_name, delta):
        if player_name not in self.players:
            raise ValueError(f"Player '{player_name}' does not exist.")
        self.players[player_name] += delta

    def get_total_score(self):
        return sum(self.players.values())

    def to_dict(self):
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "players": self.players
        }

    @classmethod
    def from_dict(cls, data):
        return cls(name=data["name"], timestamp=data["timestamp"], players=data["players"])

# --------------------------
# Utility Functions
# --------------------------
def load_games():
    try:
        with open("games.json", "r") as file:
            games_data = json.load(file)
        return [Game.from_dict(data) for data in games_data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_games(games):
    with open("games.json", "w") as file:
        json.dump([game.to_dict() for game in games], file)

# --------------------------
# HomeScreen Class
# --------------------------
class HomeScreen(BoxLayout):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager
        self.orientation = 'vertical'
        self.spacing = 20
        self.padding = 20

        self.add_widget(Label(
            text="GameCounter++",
            font_size='32sp',
            bold=True,
            size_hint=(1, 0.2)
        ))

        start_button = Button(
            text="Start New Game",
            font_size='20sp',
            size_hint=(1, 0.2),
            on_press=self.start_new_game
        )
        self.add_widget(start_button)

        self.add_widget(Label(
            text="Previous Games:",
            font_size='20sp',
            bold=True,
            size_hint=(1, 0.1)
        ))

        self.scroll = ScrollView(size_hint=(1, 0.5))
        self.previous_games_list = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.previous_games_list.bind(minimum_height=self.previous_games_list.setter('height'))
        self.scroll.add_widget(self.previous_games_list)
        self.add_widget(self.scroll)

        self.load_previous_games()

    def load_previous_games(self):
        games = load_games()
        sorted_games = sorted(games, key=lambda g: datetime.strptime(g.timestamp, "%Y-%m-%d %H:%M:%S"), reverse=True)

        self.previous_games_list.clear_widgets()
        for game in sorted_games:
            button = Button(
                text=self.truncate_text(game.name, 25),
                size_hint_y=None,
                height=50,
                on_press=lambda instance, g=game: self.load_game(g)
            )
            self.previous_games_list.add_widget(button)

    def truncate_text(self, text, max_length):
        return text if len(text) <= max_length else text[:max_length - 3] + "..."

    def start_new_game(self, instance):
        games = load_games()
        existing_names = {game.name for game in games}

        new_game_name = "New Game"
        if new_game_name in existing_names:
            new_game_name = f"{new_game_name} {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        new_game = Game(name=new_game_name)
        games.append(new_game)
        save_games(games)

        game_screen = self.screen_manager.get_screen("game_screen").children[0]
        game_screen.load_game(new_game)
        self.screen_manager.current = "game_screen"

    def load_game(self, game):
        game_screen = self.screen_manager.get_screen("game_screen").children[0]
        game_screen.load_game(game)
        self.screen_manager.current = "game_screen"

# --------------------------
# GameScreen Class
# --------------------------
class GameScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_game = None
        self.orientation = 'vertical'

        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)

        back_button = Button(
            text="<",
            size_hint=(0.1, 1),
            on_press=self.go_back
        )
        header.add_widget(back_button)

        self.title_button = Button(
            text="",
            font_size='24sp',
            size_hint=(0.8, 1),
            on_press=self.edit_game_name
        )
        header.add_widget(self.title_button)

        delete_button = Button(
            text="X",
            size_hint=(0.1, 1),
            background_color=(1, 0, 0, 1),
            color=(1, 1, 1, 1),
            on_press=self.confirm_delete_game
        )
        header.add_widget(delete_button)

        self.add_widget(header)

        self.total_score_label = Label(
            text="Total: 0",
            font_size='18sp',
            size_hint=(1, 0.1)
        )
        self.add_widget(self.total_score_label)

        player_scroll_view = ScrollView(size_hint=(1, 0.6))
        self.player_list = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.player_list.bind(minimum_height=self.player_list.setter('height'))
        player_scroll_view.add_widget(self.player_list)
        self.add_widget(player_scroll_view)

        add_player_button = Button(
            text="+ Add Player",
            size_hint=(1, 0.1),
            on_press=self.add_player
        )
        self.add_widget(add_player_button)

    def confirm_delete_game(self, instance):
        def delete_game(instance):
            games = load_games()
            games = [g for g in games if g.name != self.current_game.name]
            save_games(games)
            App.get_running_app().root.current = "home"
            popup.dismiss()

        def cancel_delete(instance):
            popup.dismiss()

        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        confirmation_label = Label(text=f"Are you sure you want to delete '{self.current_game.name}'?")
        button_layout = BoxLayout(orientation='horizontal', spacing=10)
        yes_button = Button(text="Yes", on_press=delete_game)
        no_button = Button(text="No", on_press=cancel_delete)
        button_layout.add_widget(yes_button)
        button_layout.add_widget(no_button)

        content.add_widget(confirmation_label)
        content.add_widget(button_layout)

        popup = Popup(title="Confirm Delete", content=content, size_hint=(0.8, 0.5))
        popup.open()

    def load_game(self, game):
        self.current_game = game
        self.title_button.text = game.name[:25]  # Limit to 25 characters
        self.total_score_label.text = f"Total: {game.get_total_score()}"
        self.player_list.clear_widgets()

        for player_name, score in game.players.items():
            self.add_player_banner(player_name, score)

    def add_player(self, instance=None):
        player_name = f"Player {len(self.current_game.players) + 1}"
        self.current_game.add_player(player_name)
        self.add_player_banner(player_name, 0)

    def add_player_banner(self, player_name, score):
        banner = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)

        name_button = Button(
            text=player_name,
            size_hint=(0.3, 1),
            on_press=lambda instance: self.edit_player_name(player_name)
        )
        banner.add_widget(name_button)

        minus_button = Button(
            text="-",
            size_hint=(0.2, 1),
            on_press=lambda instance: self.update_score(player_name, -1)
        )
        banner.add_widget(minus_button)

        score_label = Label(
            text=str(score),
            size_hint=(0.2, 1),
            halign="center",
            valign="middle"
        )
        score_label.bind(size=score_label.setter('text_size'))
        banner.add_widget(score_label)

        plus_button = Button(
            text="+",
            size_hint=(0.2, 1),
            on_press=lambda instance: self.update_score(player_name, 1)
        )
        banner.add_widget(plus_button)

        more_button = Button(
            text="...",
            size_hint=(0.1, 1),
            on_press=lambda instance: self.show_advanced_popup(player_name)
        )
        banner.add_widget(more_button)

        self.player_list.add_widget(banner)

    def show_advanced_popup(self, player_name):
        def adjust_score(value):
            nonlocal current_score
            current_score += value
            header_label.text = f"Starting: {starting_score} -> Current: {current_score}"

        def apply_custom_score():
            try:
                value = int(custom_input.text.strip()) if custom_input.text.strip() else 0
                adjust_score(value)
                self.current_game.update_score(player_name, current_score - starting_score)
                self.load_game(self.current_game)
                popup.dismiss()
            except ValueError:
                error_label.text = "Enter a valid number!"

        starting_score = self.current_game.players[player_name]
        current_score = starting_score

        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        header_label = Label(
            text=f"Starting: {starting_score} -> Current: {current_score}",
            font_size='20sp',
            size_hint_y=None,
            height=40
        )
        content.add_widget(header_label)

        button_layout = GridLayout(cols=6, spacing=5, size_hint_y=None, height=120)
        for val in [-100, -25, -5, 5, 25, 100]:
            score_button = Button(
                text=f"{val:+}",
                size_hint_y=None,
                height=40,
                on_press=lambda instance, v=val: adjust_score(v)
            )
            button_layout.add_widget(score_button)

        custom_input = TextInput(hint_text="Enter custom value", multiline=False, size_hint_y=None, height=50)
        error_label = Label(text="", size_hint_y=None, height=20, color=(1, 0, 0, 1))
        apply_button = Button(
            text="Apply",
            size_hint_y=None,
            height=50,
            on_press=lambda instance: apply_custom_score()
        )

        content.add_widget(button_layout)
        content.add_widget(custom_input)
        content.add_widget(error_label)
        content.add_widget(apply_button)

        popup = Popup(title="Adjust Score", content=content, size_hint=(0.8, 0.5))
        popup.open()

    def update_score(self, player_name, delta):
        self.current_game.update_score(player_name, delta)
        self.load_game(self.current_game)

    def edit_player_name(self, player_name):
        def set_new_name(instance):
            new_name = name_input.text.strip()
            if new_name:
                if new_name in self.current_game.players:
                    error_label.text = "Player name already exists!"
                else:
                    self.current_game.players[new_name] = self.current_game.players.pop(player_name)
                    self.load_game(self.current_game)
                    popup.dismiss()

        name_input = TextInput(text=player_name, multiline=False)
        save_button = Button(text="Save", size_hint=(1, 0.2), on_press=set_new_name)
        error_label = Label(text="", color=(1, 0, 0, 1))

        popup_content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        popup_content.add_widget(name_input)
        popup_content.add_widget(error_label)
        popup_content.add_widget(save_button)

        popup = Popup(title="Edit Player Name", content=popup_content, size_hint=(0.7, 0.5))
        popup.open()

    def edit_game_name(self, instance):
        def set_new_name(instance):
            new_name = name_input.text.strip()
            if new_name:
                self.current_game.name = new_name
                self.title_button.text = new_name[:25]
                save_games(load_games())
            popup.dismiss()

        name_input = TextInput(text=self.current_game.name, multiline=False)
        save_button = Button(text="Save", size_hint=(1, 0.2), on_press=set_new_name)

        popup_content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        popup_content.add_widget(name_input)
        popup_content.add_widget(save_button)

        popup = Popup(title="Edit Game Name", content=popup_content, size_hint=(0.7, 0.5))
        popup.open()

    def go_back(self, instance):
        games = load_games()
        for game in games:
            if game.name == self.current_game.name:
                game.players = self.current_game.players
                break
        else:
            games.append(self.current_game)
        save_games(games)
        App.get_running_app().root.current = "home"

# --------------------------
# Main App Class
# --------------------------
class CardGameApp(App):
    def build(self):
        screen_manager = ScreenManager()

        home_screen_widget = HomeScreen(screen_manager)
        home_screen = Screen(name="home")
        home_screen.add_widget(home_screen_widget)
        home_screen.bind(on_pre_enter=lambda instance: home_screen_widget.load_previous_games())
        screen_manager.add_widget(home_screen)

        game_screen = Screen(name="game_screen")
        game_screen.add_widget(GameScreen())
        screen_manager.add_widget(game_screen)

        return screen_manager

if __name__ == "__main__":
    CardGameApp().run()
