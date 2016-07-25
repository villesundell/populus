import os
import time
import signal

import click

from populus.utils.chain import (
    get_datadir,
)
from populus.chain import (
    reset_chain,
)

from .main import main


@main.group()
def chain():
    """
    Wrapper around `geth`.
    """
    pass


@chain.command('reset')
@click.argument('name', nargs=1, default="default")
@click.option('--confirm/--no-confirm', default=True)
def chain_reset(name, confirm):
    """
    Reset a test chain
    """
    # TODO: from `main` command
    project_dir = os.getcwd()
    data_dir = get_datadir(project_dir, name)
    if confirm:
        confirmation_message = (
            "Are you sure you want to reset blockchain {0}: {1}".format(
                name,
                data_dir,
            )
        )
        if not click.confirm(confirmation_message):
            raise click.Abort()
    reset_chain(data_dir)


@chain.command('run')
@click.argument('name', nargs=1, default="default")
@click.option('--mine/--no-mine', default=True)
@click.option(
    '--verbosity', default=5,
    help="""
    Set verbosity of the logging output. Default is 5, Range is 0-6.
    """)
def chain_run(name, mine, verbosity, active):
    """
    Run a geth node.
    """
    project_dir = os.getcwd()
    data_dir = get_geth_data_dir(project_dir, name)
    logfile_path = get_geth_logfile_path(data_dir)

    ensure_account_exists(data_dir)

    kwargs = {
        "logfile": logfile_path,
        "verbosity": "%d" % verbosity
        }

    command, proc = run_geth_node(data_dir, mine=mine, **kwargs)

    click.echo("Running: '{0}'".format(' '.join(command)))

    if active:
        set_active_data_dir(project_dir, name)

    try:
        while True:
            out_line = proc.get_stdout_nowait()
            if out_line:
                click.echo(out_line, nl=False)

            err_line = proc.get_stderr_nowait()
            if err_line:
                click.echo(err_line, nl=False)

            if err_line is None and out_line is None:
                time.sleep(0.2)
    except KeyboardInterrupt:
        try:
            proc.send_signal(signal.SIGINT)
            # Give the subprocess a SIGINT and give it a few seconds to
            # cleanup.
            utils.wait_for_popen(proc)
            while not proc.stdout_queue.empty() or not proc.stderr_queue.empty():
                out_line = proc.get_stdout_nowait()
                if out_line:
                    click.echo(out_line, nl=False)

                err_line = proc.get_stderr_nowait()
                if err_line:
                    click.echo(err_line, nl=False)
        except:
            # Try a harder termination.
            proc.terminate()
            utils.wait_for_popen(proc, 2)
    if proc.poll() is None:
        # Force it to kill if it hasn't exited already.
        proc.kill()
    if proc.returncode:
        raise click.ClickException("Error shutting down geth process.")
