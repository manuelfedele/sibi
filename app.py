import typer

from sibi import Sibi

app = typer.Typer()


@app.command()
def run():
    server = Sibi()
    server.run()


if __name__ == "__main__":
    app()
