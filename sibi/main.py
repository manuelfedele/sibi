import sys

import typer
from loguru import logger

from sibi import Sibi

fmt = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: ^8}</level> | "
    "<cyan>{name: <20}</cyan> | <cyan>{function: <20}</cyan> | "
    "<cyan>{line: ^4}</cyan> | <level>{message}</level>"
)

app = typer.Typer()


@app.command()
def run(
    client_id: int = typer.Option(
        0, help="The clientId for TWS (0 is 'master' clientId)", prompt=True
    ),
    tws_host: str = typer.Option(
        "localhost", help="The IP address of TWS", prompt=True
    ),
    tws_port: int = typer.Option(7498, help="The PORT of TWS", prompt=True),
    tws_max_connections: int = typer.Option(49, help="Max concurrent request to TWS"),
    xmlrpc_port: int = typer.Option(7080, help="XMLRPC interface exposed port"),
    log_level: str = typer.Option("DEBUG", help="Log level"),
):
    logger.configure(
        handlers=[
            {"sink": sys.stdout, "format": fmt, "level": log_level},
        ],
    )
    server = Sibi(client_id, tws_host, tws_port, tws_max_connections, xmlrpc_port)

    logger.info(f"Connecting to {tws_host}:{tws_port} (id: {client_id})")
    logger.info(f"XMLRPC Proxy will be exposed on http://localhost:{xmlrpc_port}")
    server.run()
