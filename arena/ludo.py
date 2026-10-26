import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import gradio as gr
from arena.board import RED, GREEN, YELLOW, BLUE, display_token
from arena.board_view import to_svg
from arena.game import Game
from arena.llm import LLM

ALL_MODEL_NAMES = LLM.all_model_names()


COLOR_DOTS = {
    RED: "🔴",
    GREEN: "🟢",
    YELLOW: "🟡",
    BLUE: "🔵"
}


def player_section(color: str, default_model: str):
    with gr.Column(scale=1, min_width=140, elem_classes=["player-panel"]):
        gr.HTML(f"<div class='player-header'><span>{COLOR_DOTS.get(color, '')}</span><b>{color}</b></div>")
        dropdown = gr.Dropdown(
            choices=ALL_MODEL_NAMES,
            value=default_model,
            show_label=False,
            container=False,
            interactive=True,
            elem_classes=["compact-dropdown"]
        )
        thoughts_panel = gr.HTML(
            value="<i>Waiting...</i>",
            elem_classes=["thoughts-panel"]
        )
    return dropdown, thoughts_panel


def get_status_html(game):
    acting_player = getattr(game.board, 'dice_player', None) or game.board.current_player
    dice_val = str(game.board.dice) if game.board.dice is not None else "-"

    if game.move_history:
        latest = game.move_history[-1]
        move_desc = f"{latest['Position']} ({latest['Result']})"
    else:
        move_desc = "Game ready"

    next_player = game.board.current_player

    return f"""<div style="text-align: center; margin-top: 10px; margin-bottom: 10px; font-size: 14px; line-height: 1.5;">
    <div><b>Player:</b> {acting_player}</div>
    <div><b>Rolled:</b> {dice_val}</div>
    <div><b>Move:</b> {move_desc}</div>
    <div><b>Next:</b> {next_player}</div>
</div>"""


def load_callback(game):
    svg = to_svg(game.board)
    msg = get_status_html(game)
    red_th = game.thoughts(RED)
    green_th = game.thoughts(GREEN)
    yellow_th = game.thoughts(YELLOW)
    blue_th = game.thoughts(BLUE)
    records = game.get_move_history()
    ratings = game.get_ratings()
    return game, svg, msg, red_th, green_th, yellow_th, blue_th, records, ratings


def move_callback(game):
    game.move()
    return load_callback(game)


def wait_with_stop_check(game, duration: float, step: float = 0.1) -> bool:
    """Sleep for duration in small steps, returning True immediately if game is stopped."""
    elapsed = 0.0
    while elapsed < duration:
        if getattr(game, "stopped", False):
            return True
        chunk = min(step, duration - elapsed)
        time.sleep(chunk)
        elapsed += chunk
    return getattr(game, "stopped", False)


def run_callback(game):
    game.is_running = True
    game.stopped = False
    while game.board.is_active() and not game.stopped:
        # Step (a): Roll the dice
        game.roll()

        # Step (b): Yield dice-roll frame to UI so dice animation & value are visibly displayed
        g, svg, msg, red_th, green_th, yellow_th, blue_th, records, ratings = load_callback(game)
        yield (
            g, svg, msg, red_th, green_th, yellow_th, blue_th, records, ratings,
            gr.update(interactive=False), gr.update(interactive=True),
            gr.update(interactive=False), gr.update(interactive=False),
            gr.update(interactive=False), gr.update(interactive=False)
        )

        # Step 2 & 4: Unconditional minimum hold for dice roll visibility (1.2s)
        # Checked in 0.1s increments so Stop Game responds instantly
        if wait_with_stop_check(game, 1.2, step=0.1):
            break

        if not game.board.is_active():
            break

        # Step (c) & (d): Call LLM for move decision and apply move
        game.resolve_move()

        # Step (e): Yield post-move frame showing updated token positions and thoughts
        g, svg, msg, red_th, green_th, yellow_th, blue_th, records, ratings = load_callback(game)
        yield (
            g, svg, msg, red_th, green_th, yellow_th, blue_th, records, ratings,
            gr.update(interactive=False), gr.update(interactive=True),
            gr.update(interactive=False), gr.update(interactive=False),
            gr.update(interactive=False), gr.update(interactive=False)
        )

        # Step 3 & 4: Post-move frame hold (0.6s) before next player's roll
        if wait_with_stop_check(game, 0.6, step=0.1):
            break

    game.is_running = False
    game.is_rolling = False
    g, svg, msg, red_th, green_th, yellow_th, blue_th, records, ratings = load_callback(game)
    yield (
        g, svg, msg, red_th, green_th, yellow_th, blue_th, records, ratings,
        gr.update(interactive=True), gr.update(interactive=False),
        gr.update(interactive=True), gr.update(interactive=True),
        gr.update(interactive=True), gr.update(interactive=True)
    )


def stop_callback(game):
    game.stopped = True
    game.is_running = False
    g, svg, msg, red_th, green_th, yellow_th, blue_th, records, ratings = load_callback(game)
    return (
        g, svg, msg, red_th, green_th, yellow_th, blue_th, records, ratings,
        gr.update(interactive=True), gr.update(interactive=False),
        gr.update(interactive=True), gr.update(interactive=True),
        gr.update(interactive=True), gr.update(interactive=True)
    )


def reset_callback(game):
    game.reset()
    game.is_running = False
    g, svg, msg, red_th, green_th, yellow_th, blue_th, records, ratings = load_callback(game)
    return (
        g, svg, msg, red_th, green_th, yellow_th, blue_th, records, ratings,
        gr.update(interactive=True), gr.update(interactive=False),
        gr.update(interactive=True), gr.update(interactive=True),
        gr.update(interactive=True), gr.update(interactive=True)
    )


def model_callback(player_color: str, game: Game, new_model: str):
    if getattr(game, "is_running", False):
        return game
    if player_color in game.players:
        game.players[player_color].switch_model(new_model)
    return game


def make_display():
    custom_css = """
    .arena-main-row {
        align-items: center;
        gap: 12px !important;
        margin-bottom: 15px;
    }
    .side-column {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        max-width: 250px;
    }
    .player-panel {
        border-radius: 8px;
        padding: 8px !important;
        width: 100% !important;
    }
    .player-header {
        font-size: 13px;
        font-weight: bold;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .compact-dropdown {
        margin-bottom: 4px !important;
    }
    .thoughts-panel {
        border-radius: 6px;
        padding: 6px;
        height: 120px;
        overflow-y: auto;
        font-size: 11px;
        line-height: 1.3;
    }
    .thoughts-content div {
        margin-bottom: 3px;
        white-space: normal;
        word-break: break-word;
    }
    .board-center-column {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    """

    with gr.Blocks(title="Ludo LLM Arena") as demo:
        game_state = gr.State(value=Game())

        # 1. Centered Header
        gr.HTML("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="font-size: 32px; font-weight: bold; margin: 0 0 10px 0; padding: 0; line-height: 1.2;">
                🎲 4-Player Ludo LLM Arena
            </h1>
            <p style="font-size: 16px; opacity: 0.85; margin: 0; padding: 0;">
                Watch 4 LLM models compete in a complete game of Ludo!
            </p>
        </div>
        """)

        # 2 & 3. 3-Part Arena Layout (LEFT: Red/Blue, CENTER: Board + Status, RIGHT: Green/Yellow)
        with gr.Row(elem_classes=["arena-main-row"]):
            # LEFT Column: Red (top-left) & Blue (bottom-left)
            with gr.Column(scale=1, min_width=210, elem_classes=["side-column"]):
                red_dropdown, red_thoughts = player_section(RED, "gemini-2.5-flash")
                gr.HTML("<div style='height: 12px;'></div>")
                blue_dropdown, blue_thoughts = player_section(BLUE, "gpt-oss-120b (OpenRouter)")

            # CENTER Column: Board SVG + Centered 4-Line Turn Status
            with gr.Column(scale=3, elem_classes=["board-center-column"]):
                board_svg = gr.HTML(label="Ludo Board View")
                status_msg = gr.HTML(value=get_status_html(Game()))

            # RIGHT Column: Green (top-right) & Yellow (bottom-right)
            with gr.Column(scale=1, min_width=210, elem_classes=["side-column"]):
                green_dropdown, green_thoughts = player_section(GREEN, "gpt-oss-20b (Groq)")
                gr.HTML("<div style='height: 12px;'></div>")
                yellow_dropdown, yellow_thoughts = player_section(YELLOW, "gpt-oss-120b (Groq)")

        # 4. Control Buttons (Run Game, Stop Game, Reset Game)
        with gr.Row():
            run_btn = gr.Button("Run Game ▶️", variant="primary", interactive=True)
            stop_btn = gr.Button("Stop Game ⏹️", variant="secondary", interactive=False)
            reset_btn = gr.Button("Reset Game 🔄", variant="stop", interactive=True)

        # 5. Game History & Leaderboard Tables (LAST)
        with gr.Row():
            with gr.Tabs():
                with gr.Tab("Game History"):
                    records_table = gr.DataFrame(label="Past Games")
                with gr.Tab("Leaderboard Ratings"):
                    ratings_table = gr.DataFrame(label="Model Ratings")

        # Callbacks
        demo.load(
            load_callback,
            inputs=[game_state],
            outputs=[
                game_state, board_svg, status_msg,
                red_thoughts, green_thoughts, yellow_thoughts, blue_thoughts,
                records_table, ratings_table
            ]
        )

        run_btn.click(
            run_callback,
            inputs=[game_state],
            outputs=[
                game_state, board_svg, status_msg,
                red_thoughts, green_thoughts, yellow_thoughts, blue_thoughts,
                records_table, ratings_table, run_btn, stop_btn,
                red_dropdown, green_dropdown, yellow_dropdown, blue_dropdown
            ]
        )

        stop_btn.click(
            stop_callback,
            inputs=[game_state],
            outputs=[
                game_state, board_svg, status_msg,
                red_thoughts, green_thoughts, yellow_thoughts, blue_thoughts,
                records_table, ratings_table, run_btn, stop_btn,
                red_dropdown, green_dropdown, yellow_dropdown, blue_dropdown
            ]
        )

        reset_btn.click(
            reset_callback,
            inputs=[game_state],
            outputs=[
                game_state, board_svg, status_msg,
                red_thoughts, green_thoughts, yellow_thoughts, blue_thoughts,
                records_table, ratings_table, run_btn, stop_btn,
                red_dropdown, green_dropdown, yellow_dropdown, blue_dropdown
            ]
        )

        red_dropdown.change(
            fn=lambda g, m: model_callback(RED, g, m),
            inputs=[game_state, red_dropdown],
            outputs=[game_state]
        )
        green_dropdown.change(
            fn=lambda g, m: model_callback(GREEN, g, m),
            inputs=[game_state, green_dropdown],
            outputs=[game_state]
        )
        yellow_dropdown.change(
            fn=lambda g, m: model_callback(YELLOW, g, m),
            inputs=[game_state, yellow_dropdown],
            outputs=[game_state]
        )
        blue_dropdown.change(
            fn=lambda g, m: model_callback(BLUE, g, m),
            inputs=[game_state, blue_dropdown],
            outputs=[game_state]
        )

    return demo


if __name__ == "__main__":
    demo = make_display()
    demo.launch(server_name="127.0.0.1")
