# -*- coding: utf-8 -*-
"""Command to install a basis set."""
import click

from aiida.cmdline.params import options as options_core
from aiida.cmdline.utils import decorators, echo

from .params import BasisSetParam
from .root import cmd_root


@cmd_root.command('show')
@click.argument('basisset', type=BasisSetParam(sub_classes=('aiida.groups:basis.set',)))
@options_core.RAW()
@decorators.with_dbenv()
def cmd_show(basis_set, raw):
    """Show details of a basis set."""
    from tabulate import tabulate

    rows = [[basis.element, basis.filename, basis.md5] for basis in basis_set.nodes]
    headers = ['Element', 'Basis', 'MD5']

    if raw:
        echo.echo(tabulate(sorted(rows), tablefmt='plain'))
    else:
        echo.echo(tabulate(sorted(rows), headers=headers))
