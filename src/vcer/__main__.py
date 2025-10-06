from .cli import app


def main() -> None:
    # Typer app is callable as entrypoint
    app()


if __name__ == "__main__":
    main()

