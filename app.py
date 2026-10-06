"""Entrypoint for running the Ludo LLM Arena."""
from arena.ludo import make_display

if __name__ == "__main__":
    demo = make_display()
    demo.launch(server_name="127.0.0.1")
