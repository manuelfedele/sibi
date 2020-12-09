import typer

from sibi import Solid

app = typer.Typer()


@app.command()
def run():
    server = Solid()
    server.run()


if __name__ == "__main__":
    app()
