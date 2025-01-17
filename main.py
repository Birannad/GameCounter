import json
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen


# --------------------------
# Game Class
# --------------------------
class Game:
    def __init__(self, name, timestamp=None, players=None):
        self.name = name
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.players = players or {}  # Dictionary: {player_name: score}

    def add_player(self, player_name):
        if player_name in self.players:
            raise ValueError(f"Player '{player_name}' already exists.")
        self.players[player_name] = 0

    def remove_player(self, player_name):
        if player_name in self.players:
            del self.players[player_name]
        else:
            raise ValueError(f"Player '{player_name}' does not exist.")

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

        # Title
        self.add_widget(Label(
            text="Card Game Counter",
            font_size='32sp',
            bold=True,
            size_hint=(1, 0.2)
        ))

        # "Start New Game" Button
        start_button = Button(
            text="Start New Game",
            font_size='20sp',
            size_hint=(1, 0.2),
            on_press=self.start_new_game
        )
        self.add_widget(start_button)

        # Previous Games Section
        self.add_widget(Label(
            text="Previous Games:",
            font_size='20sp',
            bold=True,
            size_hint=(1, 0.1)
        ))

        # Scrollable list of previous games
        self.scroll = ScrollView(size_hint=(1, 0.5))
        self.previous_games_list = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.previous_games_list.bind(minimum_height=self.previous_games_list.setter('height'))
        self.scroll.add_widget(self.previous_games_list)
        self.add_widget(self.scroll)

        # Load previous games
        self.load_previous_games()

    def load_previous_games(self):
        games = load_games()
        self.previous_games_list.clear_widgets()
        for game in games:
            button = Button(
                text=game.name,
                size_hint_y=None,
                height=40,
                on_press=lambda instance, g=game: self.load_game(g)
            )
            self.previous_games_list.add_widget(button)

    def start_new_game(self, instance):
        games = load_games()
        existing_names = {game.name for game in games}

        new_game_name = "New Game"
        if new_game_name in existing_names:
            new_game_name = f"{new_game_name} {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        new_game = Game(name=new_game_name)
        games.append(new_game)
        save_games(games)

        # Load the new game into GameScreen
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

        # Header with back button
        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)
        back_button = Button(
            text="<",
            size_hint=(0.1, 1),
            on_press=self.go_back
        )
        header.add_widget(back_button)

        self.title_label = Label(
            text="",
            font_size='24sp',
            size_hint=(0.8, 1),
            halign="center",
            valign="middle"
        )
        self.title_label.bind(size=self.title_label.setter('text_size'))
        header.add_widget(self.title_label)
        self.add_widget(header)

        # Total score label
        self.total_score_label = Label(
            text="Total: 0",
            font_size='18sp',
            size_hint=(1, 0.1)
        )
        self.add_widget(self.total_score_label)

        # Player list
        self.player_list = BoxLayout(orientation='vertical', spacing=10, size_hint=(1, 0.8))
        self.add_widget(self.player_list)

        # Add player button
        add_player_button = Button(
            text="+ Add Player",
            size_hint=(1, 0.1),
            on_press=self.add_player
        )
        self.add_widget(add_player_button)

    def load_game(self, game):
        self.current_game = game
        self.title_label.text = game.name
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

        # Player name button
        name_button = Button(
            text=player_name,
            size_hint=(0.4, 1),
            on_press=lambda instance: self.edit_player_name(player_name)
        )
        banner.add_widget(name_button)

        # Score adjustment buttons
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

        self.player_list.add_widget(banner)

    def update_score(self, player_name, delta):
        self.current_game.update_score(player_name, delta)
        self.load_game(self.current_game)

    def edit_player_name(self, player_name):
        def set_new_name(instance):
            new_name = name_input.text.strip()
            if new_name:
                self.current_game.players[new_name] = self.current_game.players.pop(player_name)
                self.load_game(self.current_game)
            popup.dismiss()

        name_input = TextInput(hint_text="Enter new name", multiline=False)
        save_button = Button(text="Save", on_press=set_new_name)
        popup_content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        popup_content.add_widget(name_input)
        popup_content.add_widget(save_button)
        popup = Popup(title="Edit Player Name", content=popup_content, size_hint=(0.7, 0.5))
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

        # Add Home Screen
        home_screen = Screen(name="home")
        home_screen.add_widget(HomeScreen(screen_manager))
        screen_manager.add_widget(home_screen)

        # Add Game Screen
        game_screen = Screen(name="game_screen")
        game_screen.add_widget(GameScreen())
        screen_manager.add_widget(game_screen)

        return screen_manager


if __name__ == "__main__":
    CardGameApp().run()
