from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Line, Ellipse, RoundedRectangle
from kivy.metrics import dp
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
import json
import math
import os
import random


# =========================================================
# COLOR PALETTE
# =========================================================

BACKGROUND_COLOR = (0.035, 0.045, 0.09, 1)
BUTTON_COLOR = (0.10, 0.13, 0.22, 1)
PRIMARY_BUTTON_COLOR = (0.08, 0.32, 0.48, 1)
SECONDARY_BUTTON_COLOR = (0.25, 0.13, 0.40, 1)

TEXT_COLOR = (0.92, 0.95, 1, 1)
MUTED_TEXT_COLOR = (0.55, 0.60, 0.70, 1)
ACCENT_COLOR = (0.15, 0.85, 1, 1)
SUCCESS_COLOR = (0.20, 0.95, 0.50, 1)
ERROR_COLOR = (1, 0.25, 0.30, 1)


# =========================================================
# TOTAL LEVELS
# =========================================================

TOTAL_LEVELS = 100


# =========================================================
# PERSISTENCE
# =========================================================

def get_progress_path():
    """Return the path used to store player progress."""
    app = App.get_running_app()

    return os.path.join(
        app.user_data_dir,
        "oneline_puzzle_progress.json",
    )


def load_progress():
    """Load saved progress or return the default progress state."""

    default_progress = {
        "unlocked": 1,
        "stars": {},
        "last_level": 1,
    }

    try:
        path = get_progress_path()

        if not os.path.exists(path):
            return default_progress

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            progress = json.load(file)

        for key, default_value in default_progress.items():
            progress.setdefault(
                key,
                default_value
            )

        return progress

    except (
        OSError,
        TypeError,
        ValueError
    ):

        return default_progress


def save_progress(progress):
    """Persist player progress to disk."""

    try:

        with open(
            get_progress_path(),
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                progress,
                file
            )

    except (
        OSError,
        TypeError,
        ValueError
    ):

        pass


# =========================================================
# AUDIO
# =========================================================

def load_sound(filename):
    """Load a sound file safely."""

    try:
        return SoundLoader.load(filename)

    except Exception:
        return None


CORRECT_SOUND = load_sound(
    "correct.wav"
)

WRONG_SOUND = load_sound(
    "wrong.wav"
)


# =========================================================
# LEVEL GENERATION
# =========================================================

def is_connected(points_count, edges):
    """Check that every point belongs to one connected graph."""

    if not edges:
        return False

    graph = {
        index: []
        for index in range(points_count)
    }

    for first, second in edges:

        graph[first].append(second)
        graph[second].append(first)

    start = next(
        (
            index
            for index in graph
            if graph[index]
        ),
        None
    )

    if start is None:
        return False

    visited = {start}
    stack = [start]

    while stack:

        current = stack.pop()

        for neighbor in graph[current]:

            if neighbor not in visited:

                visited.add(neighbor)
                stack.append(neighbor)

    active_points = {
        index
        for index in graph
        if graph[index]
    }

    return visited == active_points


def has_euler_solution(points_count, edges):
    """Check whether the graph can be drawn in one stroke."""

    if not is_connected(
        points_count,
        edges
    ):
        return False

    degrees = [
        0
        for _ in range(points_count)
    ]

    for first, second in edges:

        degrees[first] += 1
        degrees[second] += 1

    odd_count = sum(
        degree % 2
        for degree in degrees
    )

    return odd_count in (0, 2)


def generate_level(level_number):
    """Generate a connected one-stroke puzzle."""

    random.seed(
        level_number * 9871
    )

    # -----------------------------------------------------
    # Difficulty
    # -----------------------------------------------------

    if level_number <= 10:

        rows, columns = 2, 3

    elif level_number <= 20:

        rows, columns = 3, 3

    elif level_number <= 30:

        rows, columns = 3, 4

    elif level_number <= 40:

        rows, columns = 4, 4

    elif level_number <= 50:

        rows, columns = 4, 5

    elif level_number <= 65:

        rows, columns = 5, 5

    elif level_number <= 80:

        rows, columns = 5, 6

    else:

        rows, columns = 6, 6

    # -----------------------------------------------------
    # Points
    # -----------------------------------------------------

    points = []

    for row in range(rows):

        for column in range(columns):

            x = (
                0.12
                +
                (
                    column
                    / max(
                        1,
                        columns - 1
                    )
                )
                * 0.76
            )

            y = (
                0.15
                +
                (
                    row
                    / max(
                        1,
                        rows - 1
                    )
                )
                * 0.70
            )

            points.append(
                (x, y)
            )

    # -----------------------------------------------------
    # Basic grid edges
    # -----------------------------------------------------

    possible_edges = []

    for row in range(rows):

        for column in range(columns):

            current = (
                row * columns
                + column
            )

            # Right
            if column < columns - 1:

                possible_edges.append(
                    (
                        current,
                        current + 1
                    )
                )

            # Down
            if row < rows - 1:

                possible_edges.append(
                    (
                        current,
                        current + columns
                    )
                )

    # -----------------------------------------------------
    # Diagonal edges
    # -----------------------------------------------------

    for row in range(rows - 1):

        for column in range(columns - 1):

            top_left = (
                row * columns
                + column
            )

            top_right = (
                row * columns
                + column
                + 1
            )

            bottom_left = (
                (row + 1) * columns
                + column
            )

            bottom_right = (
                (row + 1) * columns
                + column
                + 1
            )

            if random.random() < 0.30:

                possible_edges.append(
                    (
                        top_left,
                        bottom_right
                    )
                )

            if random.random() < 0.15:

                possible_edges.append(
                    (
                        top_right,
                        bottom_left
                    )
                )

    # -----------------------------------------------------
    # Remove duplicate edges
    # -----------------------------------------------------

    unique_edges = []
    seen = set()

    for first, second in possible_edges:

        edge = tuple(
            sorted(
                (
                    first,
                    second
                )
            )
        )

        if edge not in seen:

            seen.add(edge)
            unique_edges.append(edge)

    possible_edges = unique_edges

    # -----------------------------------------------------
    # Try many times until a valid puzzle is created
    # -----------------------------------------------------

    for attempt in range(200):

        random.shuffle(
            possible_edges
        )

        selected_edges = []

        # -------------------------------------------------
        # Start with a connected tree.
        # -------------------------------------------------

        connected = {0}

        remaining = list(
            range(
                1,
                len(points)
            )
        )

        while remaining:

            new_point = random.choice(
                remaining
            )

            possible_connections = [
                edge
                for edge in possible_edges
                if (
                    (
                        edge[0] == new_point
                        and edge[1] in connected
                    )
                    or
                    (
                        edge[1] == new_point
                        and edge[0] in connected
                    )
                )
            ]

            if not possible_connections:
                break

            edge = random.choice(
                possible_connections
            )

            selected_edges.append(edge)

            connected.add(
                new_point
            )

            remaining.remove(
                new_point
            )

        # -------------------------------------------------
        # If not all points connected, retry.
        # -------------------------------------------------

        if len(connected) != len(points):
            continue

        # -------------------------------------------------
        # Add extra edges.
        # -------------------------------------------------

        candidates = [
            edge
            for edge in possible_edges
            if edge not in selected_edges
        ]

        random.shuffle(candidates)

        target_edges = min(
            len(possible_edges),
            5 + level_number // 2
        )

        while (
            len(selected_edges)
            < target_edges
            and len(candidates) >= 2
        ):

            first_edge = candidates.pop()

            second_edge = candidates.pop()

            test_edges = (
                selected_edges
                + [
                    first_edge,
                    second_edge
                ]
            )

            if has_euler_solution(
                len(points),
                test_edges
            ):

                selected_edges = test_edges

        # -------------------------------------------------
        # Validate final puzzle.
        # -------------------------------------------------

        if has_euler_solution(
            len(points),
            selected_edges
        ):

            return {
                "name": (
                    f"Puzzle {level_number}"
                ),
                "points": points,
                "edges": selected_edges,
            }

    # -----------------------------------------------------
    # Guaranteed fallback
    # -----------------------------------------------------

    fallback_edges = []

    for index in range(
        len(points) - 1
    ):

        fallback_edges.append(
            (
                index,
                index + 1
            )
        )

    return {
        "name": f"Puzzle {level_number}",
        "points": points,
        "edges": fallback_edges,
    }


# =========================================================
# CREATE 100 LEVELS
# =========================================================

LEVELS = {
    level_number: generate_level(
        level_number
    )
    for level_number in range(
        1,
        TOTAL_LEVELS + 1
    )
}


# =========================================================
# BUTTON COMPONENT
# =========================================================

class GameButton(Button):
    """Styled button used throughout the application."""

    def __init__(
        self,
        background_color=BUTTON_COLOR,
        **kwargs
    ):

        super().__init__(**kwargs)

        self.background_normal = ""
        self.background_down = ""
        self.color = TEXT_COLOR
        self.bold = True
        self.font_size = dp(16)
        self.background_color = (
            0,
            0,
            0,
            0
        )

        self.button_color = (
            background_color
        )

        with self.canvas.before:

            Color(
                *self.button_color
            )

            self.background_shape = (
                RoundedRectangle(
                    pos=self.pos,
                    size=self.size,
                    radius=[
                        (dp(16), dp(16)),
                        (dp(16), dp(16)),
                        (dp(16), dp(16)),
                        (dp(16), dp(16)),
                    ],
                )
            )

        self.bind(
            pos=self._update_background,
            size=self._update_background,
        )

    def _update_background(self, *_args):

        self.background_shape.pos = (
            self.pos
        )

        self.background_shape.size = (
            self.size
        )


# =========================================================
# PUZZLE BOARD
# =========================================================

class PuzzleBoard(Widget):
    """Interactive board for drawing a single continuous path."""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.points = []
        self.edges = []
        self.visited_edges = set()
        self.path = []
        self.current_node = None
        self.is_drawing = False
        self.on_complete = None
        self.on_wrong = None

        self.bind(
            pos=self.redraw,
            size=self.redraw,
        )

    def set_puzzle(
        self,
        points,
        edges
    ):

        self.points = points
        self.edges = edges
        self.visited_edges = set()
        self.path = []
        self.current_node = None
        self.is_drawing = False

        self.redraw()

    def get_screen_point(
        self,
        point
    ):

        return (
            self.x
            + point[0] * self.width,

            self.y
            + point[1] * self.height,
        )

    def get_nearest_node(
        self,
        x,
        y
    ):

        nearest = None
        minimum_distance = dp(50)

        for index, point in enumerate(
            self.points
        ):

            point_x, point_y = (
                self.get_screen_point(
                    point
                )
            )

            distance = math.sqrt(
                (x - point_x) ** 2
                +
                (y - point_y) ** 2
            )

            if distance < minimum_distance:

                minimum_distance = distance
                nearest = index

        return nearest

    def find_edge(
        self,
        first_node,
        second_node
    ):

        for index, edge in enumerate(
            self.edges
        ):

            first, second = edge

            if (
                (
                    first == first_node
                    and second == second_node
                )
                or
                (
                    first == second_node
                    and second == first_node
                )
            ):

                return index

        return None

    def on_touch_down(
        self,
        touch
    ):

        if not self.collide_point(
            *touch.pos
        ):

            return super().on_touch_down(
                touch
            )

        node = self.get_nearest_node(
            *touch.pos
        )

        if node is None:
            return True

        if self.current_node is None:

            self.current_node = node
            self.path = [node]
            self.is_drawing = True

            self.redraw()

            return True

        if node != self.current_node:

            if self.on_wrong:
                self.on_wrong()

            return True

        self.is_drawing = True

        return True

    def on_touch_move(
        self,
        touch
    ):

        if not self.is_drawing:
            return True

        node = self.get_nearest_node(
            *touch.pos
        )

        if (
            node is None
            or node == self.current_node
        ):

            return True

        edge_index = self.find_edge(
            self.current_node,
            node
        )

        if (
            edge_index is None
            or edge_index in self.visited_edges
        ):

            return True

        self.visited_edges.add(
            edge_index
        )

        self.path.append(
            node
        )

        self.current_node = node

        self.redraw()

        if len(
            self.visited_edges
        ) == len(self.edges):

            self.is_drawing = False

            if self.on_complete:

                Clock.schedule_once(
                    lambda _dt:
                    self.on_complete(),
                    0.1,
                )

        return True

    def on_touch_up(
        self,
        _touch
    ):

        self.is_drawing = False

        return True

    def reset(self):

        self.visited_edges.clear()
        self.path.clear()
        self.current_node = None
        self.is_drawing = False

        self.redraw()

    def redraw(
        self,
        *_args
    ):

        self.canvas.clear()

        with self.canvas:

            Color(
                0.055,
                0.065,
                0.12,
                1
            )

            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[
                    (dp(25), dp(25)),
                    (dp(25), dp(25)),
                    (dp(25), dp(25)),
                    (dp(25), dp(25)),
                ],
            )

            Color(
                0.14,
                0.20,
                0.32,
                1
            )

            Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    dp(25),
                ),
                width=1.2,
            )

            for index, edge in enumerate(
                self.edges
            ):

                first, second = edge

                x1, y1 = (
                    self.get_screen_point(
                        self.points[first]
                    )
                )

                x2, y2 = (
                    self.get_screen_point(
                        self.points[second]
                    )
                )

                if index in self.visited_edges:

                    Color(
                        0.05,
                        0.75,
                        1,
                        0.20
                    )

                    Line(
                        points=[
                            x1,
                            y1,
                            x2,
                            y2,
                        ],
                        width=dp(10),
                    )

                    Color(
                        *ACCENT_COLOR
                    )

                    Line(
                        points=[
                            x1,
                            y1,
                            x2,
                            y2,
                        ],
                        width=dp(4),
                    )

                else:

                    Color(
                        0.18,
                        0.23,
                        0.34,
                        1
                    )

                    Line(
                        points=[
                            x1,
                            y1,
                            x2,
                            y2,
                        ],
                        width=dp(3),
                    )

            for index, point in enumerate(
                self.points
            ):

                x, y = (
                    self.get_screen_point(
                        point
                    )
                )

                if index == self.current_node:

                    Color(
                        0.10,
                        0.75,
                        1,
                        0.20
                    )

                    Ellipse(
                        pos=(
                            x - dp(22),
                            y - dp(22),
                        ),
                        size=(
                            dp(44),
                            dp(44),
                        ),
                    )

                Color(
                    *ACCENT_COLOR
                )

                Ellipse(
                    pos=(
                        x - dp(10),
                        y - dp(10),
                    ),
                    size=(
                        dp(20),
                        dp(20),
                    ),
                )

                Color(
                    0.90,
                    0.98,
                    1,
                    1
                )

                Ellipse(
                    pos=(
                        x - dp(4),
                        y - dp(4),
                    ),
                    size=(
                        dp(8),
                        dp(8),
                    ),
                )


# =========================================================
# HOME SCREEN
# =========================================================

class HomeScreen(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(25),
            spacing=dp(15),
        )

        root.add_widget(
            Widget(
                size_hint_y=0.22
            )
        )

        root.add_widget(
            Label(
                text=(
                    "[b]ONE LINE[/b]\n"
                    "[b]PUZZLE[/b]"
                ),
                markup=True,
                font_size=dp(40),
                color=TEXT_COLOR,
                halign="center",
            )
        )

        root.add_widget(
            Label(
                text=(
                    f"{TOTAL_LEVELS} "
                    "puzzles • One stroke"
                ),
                font_size=dp(15),
                color=MUTED_TEXT_COLOR,
                size_hint_y=None,
                height=dp(40),
            )
        )

        root.add_widget(
            Widget(
                size_hint_y=0.10
            )
        )

        play_button = GameButton(
            text="PLAY",
            background_color=(
                PRIMARY_BUTTON_COLOR
            ),
            size_hint_y=None,
            height=dp(60),
        )

        play_button.bind(
            on_release=self.play
        )

        root.add_widget(
            play_button
        )

        levels_button = GameButton(
            text="LEVELS",
            background_color=(
                SECONDARY_BUTTON_COLOR
            ),
            size_hint_y=None,
            height=dp(55),
        )

        levels_button.bind(
            on_release=self.open_levels
        )

        root.add_widget(
            levels_button
        )

        root.add_widget(
            Widget(
                size_hint_y=0.30
            )
        )

        self.add_widget(root)

    def play(self, *_args):

        app = App.get_running_app()

        level = app.progress.get(
            "last_level",
            1
        )

        unlocked = app.progress.get(
            "unlocked",
            1
        )

        level = min(
            max(level, 1),
            unlocked,
            TOTAL_LEVELS
        )

        self.manager.get_screen(
            "puzzle"
        ).load_level(level)

        self.manager.current = "puzzle"

    def open_levels(self, *_args):

        self.manager.get_screen(
            "levels"
        ).refresh()

        self.manager.current = "levels"


# =========================================================
# LEVEL SELECTION SCREEN
# =========================================================

class LevelScreen(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(15),
        )

        title_bar = BoxLayout(
            size_hint_y=None,
            height=dp(55),
            spacing=dp(10),
        )

        back_button = GameButton(
            text="‹",
            background_color=BUTTON_COLOR,
            font_size=dp(30),
            size_hint_x=None,
            width=dp(55),
        )

        back_button.bind(
            on_release=lambda _button:
            setattr(
                self.manager,
                "current",
                "home",
            )
        )

        title_bar.add_widget(
            back_button
        )

        title_bar.add_widget(
            Label(
                text=(
                    f"[b]{TOTAL_LEVELS} "
                    "LEVELS[/b]"
                ),
                markup=True,
                font_size=dp(24),
                color=TEXT_COLOR,
            )
        )

        root.add_widget(
            title_bar
        )

        self.grid = GridLayout(
            cols=2,
            spacing=dp(12),
            padding=dp(2),
            size_hint_y=None,
        )

        self.grid.bind(
            minimum_height=
            self.grid.setter(
                "height"
            )
        )

        scroll_view = ScrollView()

        scroll_view.add_widget(
            self.grid
        )

        root.add_widget(
            scroll_view
        )

        self.add_widget(root)

    def refresh(self):

        self.grid.clear_widgets()

        app = App.get_running_app()

        unlocked = app.progress.get(
            "unlocked",
            1
        )

        stars = app.progress.get(
            "stars",
            {}
        )

        last_level = app.progress.get(
            "last_level",
            1
        )

        for level in range(
            1,
            TOTAL_LEVELS + 1
        ):

            locked = level > unlocked

            if locked:

                text = (
                    f"🔒\nLEVEL {level}"
                )

                background_color = (
                    0.06,
                    0.07,
                    0.11,
                    1
                )

            else:

                star_count = int(
                    stars.get(
                        str(level),
                        0
                    )
                )

                if star_count == 3:

                    star_text = (
                        "★ ★ ★"
                    )

                elif star_count == 2:

                    star_text = (
                        "★ ★ ☆"
                    )

                elif star_count == 1:

                    star_text = (
                        "★ ☆ ☆"
                    )

                else:

                    star_text = (
                        "☆ ☆ ☆"
                    )

                if level == last_level:

                    text = (
                        f"[b]LEVEL "
                        f"{level}[/b]\n"
                        f"LAST PLAYED\n"
                        f"{star_text}"
                    )

                    background_color = (
                        PRIMARY_BUTTON_COLOR
                    )

                else:

                    text = (
                        f"[b]LEVEL "
                        f"{level}[/b]\n"
                        f"{star_text}"
                    )

                    background_color = (
                        BUTTON_COLOR
                    )

            button = GameButton(
                text=text,
                markup=True,
                background_color=(
                    background_color
                ),
                size_hint_y=None,
                height=dp(95),
            )

            if not locked:

                button.bind(
                    on_release=
                    lambda
                    _button,
                    selected_level=level:
                    self.open_level(
                        selected_level
                    )
                )

            self.grid.add_widget(
                button
            )

    def open_level(self, level):

        self.manager.get_screen(
            "puzzle"
        ).load_level(level)

        self.manager.current = "puzzle"


# =========================================================
# PUZZLE SCREEN
# =========================================================

class PuzzleScreen(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.level = 1
        self.lives = 3
        self.completed = False

        root = BoxLayout(
            orientation="vertical",
            padding=[
                dp(15),
                dp(18)
            ],
            spacing=dp(10),
        )

        top_bar = BoxLayout(
            size_hint_y=None,
            height=dp(58),
            spacing=dp(8),
        )

        back_button = GameButton(
            text="‹",
            background_color=BUTTON_COLOR,
            font_size=dp(30),
            size_hint_x=None,
            width=dp(52),
        )

        back_button.bind(
            on_release=self.go_home
        )

        top_bar.add_widget(
            back_button
        )

        level_info = BoxLayout(
            orientation="vertical"
        )

        self.level_label = Label(
            text="[b]LEVEL 1[/b]",
            markup=True,
            font_size=dp(20),
            color=TEXT_COLOR,
        )

        self.name_label = Label(
            text="Puzzle 1",
            font_size=dp(12),
            color=MUTED_TEXT_COLOR,
        )

        level_info.add_widget(
            self.level_label
        )

        level_info.add_widget(
            self.name_label
        )

        top_bar.add_widget(
            level_info
        )

        self.lives_label = Label(
            text="♥ ♥ ♥",
            font_size=dp(19),
            color=ERROR_COLOR,
            size_hint_x=None,
            width=dp(95),
        )

        top_bar.add_widget(
            self.lives_label
        )

        root.add_widget(
            top_bar
        )

        self.message = Label(
            text=(
                "Touch a corner and drag "
                "to a connected corner"
            ),
            font_size=dp(13),
            color=MUTED_TEXT_COLOR,
            size_hint_y=None,
            height=dp(35),
        )

        root.add_widget(
            self.message
        )

        self.board = PuzzleBoard()

        self.board.on_complete = (
            self.puzzle_complete
        )

        self.board.on_wrong = (
            self.wrong_move
        )

        root.add_widget(
            self.board
        )

        self.result = Label(
            text="",
            font_size=dp(23),
            bold=True,
            size_hint_y=None,
            height=dp(38),
        )

        root.add_widget(
            self.result
        )

        button_bar = BoxLayout(
            size_hint_y=None,
            height=dp(55),
            spacing=dp(8),
        )

        retry_button = GameButton(
            text="RETRY",
            background_color=BUTTON_COLOR,
        )

        retry_button.bind(
            on_release=
            lambda _button:
            self.retry()
        )

        button_bar.add_widget(
            retry_button
        )

        hint_button = GameButton(
            text="HINT",
            background_color=(
                SECONDARY_BUTTON_COLOR
            ),
        )

        hint_button.bind(
            on_release=
            lambda _button:
            self.hint()
        )

        button_bar.add_widget(
            hint_button
        )

        self.next_button = GameButton(
            text="NEXT →",
            background_color=(
                PRIMARY_BUTTON_COLOR
            ),
        )

        self.next_button.disabled = True

        self.next_button.bind(
            on_release=
            lambda _button:
            self.next_level()
        )

        button_bar.add_widget(
            self.next_button
        )

        root.add_widget(
            button_bar
        )

        self.add_widget(root)

    def load_level(self, level):

        self.level = level
        self.lives = 3
        self.completed = False

        app = App.get_running_app()

        app.progress["last_level"] = (
            level
        )

        save_progress(
            app.progress
        )

        level_data = LEVELS[level]

        self.level_label.text = (
            f"[b]LEVEL {level}[/b]"
        )

        self.name_label.text = (
            level_data["name"]
        )

        self.message.text = (
            "Touch a corner and drag "
            "to a connected corner"
        )

        self.result.text = ""

        self.next_button.disabled = True

        self.update_lives()

        self.board.set_puzzle(
            level_data["points"],
            level_data["edges"],
        )

    def update_lives(self):

        self.lives_label.text = "".join(
            "♥ "
            if index < self.lives
            else "♡ "
            for index in range(3)
        )

    def wrong_move(self):

        if self.completed:
            return

        self.lives -= 1

        self.update_lives()

        self.result.text = (
            "✗ WRONG!"
        )

        self.result.color = (
            ERROR_COLOR
        )

        self.message.text = (
            "You must start from the "
            "glowing corner."
        )

        if WRONG_SOUND:

            try:

                WRONG_SOUND.stop()
                WRONG_SOUND.play()

            except Exception:
                pass

        if self.lives <= 0:

            self.message.text = (
                "No lives left! Tap RETRY."
            )

        self.board.is_drawing = False

    def puzzle_complete(self):

        if self.completed:
            return

        self.completed = True

        self.result.text = (
            "✓ COMPLETE!"
        )

        self.result.color = (
            SUCCESS_COLOR
        )

        self.message.text = (
            "Great job! Puzzle completed."
        )

        if CORRECT_SOUND:

            try:

                CORRECT_SOUND.stop()
                CORRECT_SOUND.play()

            except Exception:
                pass

        earned_stars = max(
            1,
            self.lives
        )

        app = App.get_running_app()

        previous_stars = int(
            app.progress["stars"].get(
                str(self.level),
                0
            )
        )

        if earned_stars > previous_stars:

            app.progress["stars"][
                str(self.level)
            ] = earned_stars

        if self.level < TOTAL_LEVELS:

            app.progress["unlocked"] = max(
                app.progress["unlocked"],
                self.level + 1,
            )

        app.progress["last_level"] = (
            self.level
        )

        save_progress(
            app.progress
        )

        if self.level < TOTAL_LEVELS:

            self.next_button.disabled = False

    def retry(self):

        self.lives = 3
        self.completed = False

        self.result.text = ""

        self.message.text = (
            "Touch a corner and drag "
            "to a connected corner"
        )

        self.next_button.disabled = True

        self.update_lives()

        self.board.reset()

    def hint(self):

        if self.completed:
            return

        if self.board.current_node is None:

            self.message.text = (
                "Start from any corner."
            )

        else:

            self.message.text = (
                "Continue from the "
                "glowing corner."
            )

    def next_level(self):

        if self.level >= TOTAL_LEVELS:

            self.result.text = (
                f"★ ALL {TOTAL_LEVELS} "
                "LEVELS COMPLETE!"
            )

            return

        self.load_level(
            self.level + 1
        )

    def go_home(self, *_args):

        self.manager.current = "home"


# =========================================================
# APPLICATION
# =========================================================

class OneLinePuzzleApp(App):

    title = "OneLine Puzzle"

    def build(self):

        self.progress = load_progress()

        screen_manager = ScreenManager()

        screen_manager.add_widget(
            HomeScreen(
                name="home"
            )
        )

        screen_manager.add_widget(
            LevelScreen(
                name="levels"
            )
        )

        screen_manager.add_widget(
            PuzzleScreen(
                name="puzzle"
            )
        )

        return screen_manager


if __name__ == "__main__":
    OneLinePuzzleApp().run()