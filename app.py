"""Production entrypoint for the upgraded Flask EHR system."""

from app import create_app

app = create_app()


def main() -> None:
    """Run the Flask development server for the EHR app."""
    app.run(debug=True)


if __name__ == "__main__":
    main()
