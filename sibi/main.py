import typer
from sibi.settings import logger
from sibi import Sibi

app = typer.Typer()


@app.command()
def run(client_id: int = typer.Option(0, help="The clientId for TWS (0 is 'master' clientId)", prompt=True),
        tws_host: str = typer.Option('localhost', help='The IP address of TWS', prompt=True),
        tws_port: int = typer.Option(7498, help='The PORT of TWS', prompt=True),
        tws_max_connections: int = typer.Option(49, help='Max concurrent request to TWS'),
        xmlrpc_port: int = typer.Option(7080, help='XMLRPC interface exposed port')):
    server = Sibi(client_id,
                  tws_host,
                  tws_port,
                  tws_max_connections,
                  xmlrpc_port)
    logger.info(f"Connecting to {tws_host}:{tws_port} (id: {client_id})")
    logger.info(f"XMLRPC Proxy will be exposed on http://localhost:{xmlrpc_port}")
    server.run()
