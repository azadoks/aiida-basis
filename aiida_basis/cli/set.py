# -*- coding: utf-8 -*-
"""Commands to inspect or modify the contents of basis sets."""
from aiida.cmdline.params import options as options_core
from aiida.cmdline.utils import decorators, echo

from ..groups.mixins import RecommendedOrbitalConfigurationMixin
from .params import arguments
from .root import cmd_root
from .utils import format_orbital_configuration


@cmd_root.group('set')
def cmd_basis_set():
    """Command group to inspect or modify the contents of basis sets."""


@cmd_basis_set.command('show')
@arguments.BASIS_SET()
@options_core.RAW()
@decorators.with_dbenv()
def cmd_basis_set_show(basis_set, raw):
    """Show the details of a basis set."""
    from tabulate import tabulate

    if isinstance(basis_set, RecommendedOrbitalConfigurationMixin):
        headers = ['Element', 'Basis', 'MD5', 'Orbital configuration']
        rows = [[
            basis.element, basis.filename, basis.md5,
            format_orbital_configuration(
                basis_set.get_recommended_orbital_configurations(elements=basis.element)[basis.element]
            )
        ] for basis in basis_set.nodes]

    else:
        headers = ['Element', 'Basis', 'MD5']
        rows = [[basis.element, basis.filename, basis.md5] for basis in basis_set.nodes]

    if raw:
        echo.echo(tabulate(sorted(rows), tablefmt='plain'))
    else:
        echo.echo(tabulate(sorted(rows), headers=headers))
