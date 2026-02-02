from __future__ import annotations

from .engine import AfyabotEngine


def run_cli() -> None:
    engine = AfyabotEngine()
    session_id = None

    print("Afyabot CLI")
    print("Type 'start' to begin, 'menu' for main menu, 'exit' to quit.")

    while True:
        user = input("> ").strip()
        if user.lower() in {"exit", "quit"}:
            break

        session_id, reply = engine.handle_message(session_id=session_id, text=user)
        print(reply)


if __name__ == "__main__":
    run_cli()
