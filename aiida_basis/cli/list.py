# -*- coding: utf-8 -*-
"""Commands to list instances of `BasisSet`."""
import click
from aiida.cmdline.params import options as options_core
from aiida.cmdline.utils import decorators, echo

from .params import options
from .root import cmd_root

PROJECTIONS_VALID = ('pk', 'uuid', 'type_string', 'label', 'description', 'count')
PROJECTIONS_DEFAULT = ('label', 'type_string', 'count')


def get_basis_sets_builder():
    """Return a query builder that will query for instances of `BasisSet` or its subclasses.

    :return: `QueryBuilder` instance
    """
    from aiida.orm import QueryBuilder
    from aiida_basis.groups.set import BasisSet

    builder = QueryBuilder().append(BasisSet)

    return builder


@cmd_root.command('list')
@options_core.PROJECT(type=click.Choice(PROJECTIONS_VALID), default=PROJECTIONS_DEFAULT)
@options_core.RAW()
@options.BASIS_SET_TYPE(default=None, help='Filter for families of with this type string.')
@decorators.with_dbenv()
def cmd_list(project, raw, basis_set_type):
    """List installed basis sets."""
    from tabulate import tabulate

    mapping_project = {
        'count': lambda family: family.count(),
    }

    if get_basis_sets_builder().count() == 0:
        echo.echo_info('no basis sets have been installed yet: use `aiida-basis install`.')
        return

    rows = []

    for group, in get_basis_sets_builder().iterall():

        if basis_set_type and basis_set_type.entry_point != group.type_string:
            continue

        row = []

        for projection in project:
            try:
                projected = mapping_project[projection](group)
            except KeyError:
                projected = getattr(group, projection)
            row.append(projected)

        rows.append(row)

    if not rows:
        echo.echo_info('no basis sets found that match the filtering criteria.')
        return

    if raw:
        echo.echo(tabulate(rows, disable_numparse=True, tablefmt='plain'))
    else:
        headers = [projection.replace('_', ' ').capitalize() for projection in project]
        echo.echo(tabulate(rows, headers=headers, disable_numparse=True))
