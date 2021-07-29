# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
"""Custom parameter types for command line interface commands."""
import typing
import pathlib

import click
import requests

from aiida.cmdline.params.types import GroupParamType
from ..utils import attempt

__all__ = ('BasisSetTypeParam', 'BasisTypeParam')


class BasisTypeParam(GroupParamType):
    """Parameter type for `click` commands to define an instance of a `BasisSet`."""

    name = 'basis_type'

    def convert(self, value, _, __):
        """Convert the entry point name to the corresponding class.

        :param value: entry point name that should correspond to subclass of `Basis` data plugin
        :return: the `Basis` subclass
        :raises: `click.BadParameter` if the entry point cannot be loaded or is not subclass of `Basis`
        """
        from aiida.common import exceptions
        from aiida.plugins import DataFactory
        from aiida_basis.data.basis import BasisData

        try:
            basis_type = DataFactory(value)
        except exceptions.EntryPointError as exception:
            raise click.BadParameter(f'`{value}` is not an existing data plugin.') from exception

        if not issubclass(basis_type, BasisData):
            raise click.BadParameter(f'`{value}` entry point is not a subclass of `BasisData`.')

        BasisData.entry_point = value

        return basis_type

    def complete(self, _, incomplete):
        """Return possible completions based on an incomplete value.

        :returns: list of tuples of valid entry points (matching incomplete) and a description
        """
        from aiida.plugins.entry_point import get_entry_point_names
        entry_points = get_entry_point_names('aiida.data')
        return [(ep, '') for ep in entry_points if (ep.startswith('basis.basis') and ep.startswith(incomplete))]


class BasisSetTypeParam(click.ParamType):
    """Parameter type for `click` commands to define a subclass of `BasisSet`."""

    name = 'basis_set_type'

    def convert(self, value, _, __):
        """Convert the entry point name to the corresponding class.

        :param value: entry point name that should correspond to subclass of `BasisSet` group plugin
        :return: the `BasisSet` subclass
        :raises: `click.BadParameter` if the entry point cannot be loaded or is not subclass of `BasisSet`
        """
        from aiida.common import exceptions
        from aiida.plugins import GroupFactory
        from aiida_basis.groups.set import BasisSet

        try:
            basis_set_type = GroupFactory(value)
        except exceptions.EntryPointError as exception:
            raise click.BadParameter(f'`{value}` is not an existing group plugin.') from exception

        if not issubclass(basis_set_type, BasisSet):
            raise click.BadParameter(f'`{value}` entry point is not a subclass of `BasisSet`.')

        BasisSet.entry_point = value

        return basis_set_type

    def complete(self, _, incomplete):
        """Return possible completions based on an incomplete value.

        :returns: list of tuples of valid entry points (matching incomplete) and a description
        """
        from aiida.plugins.entry_point import get_entry_point_names
        entry_points = get_entry_point_names('aiida.groups')
        return [(ep, '') for ep in entry_points if (ep.startswith('basis.set') and ep.startswith(incomplete))]


class BasisSetParam(GroupParamType):
    """Parameter for `click` commands to define an instance of a `BasisSet`."""

    name = 'basis_set'


class PathOrUrl(click.Path):
    """Extension of ``click``'s ``Path``-type that also supports URLs."""

    name = 'PathOrUrl'

    def convert(self, value, param, ctx) -> typing.Union[pathlib.Path, bytes]:  # pylint: disable=unsubscriptable-object
        """Convert the string value to the desired value.

        If the ``value`` corresponds to a valid path on the local filesystem, return it as a ``pathlib.Path`` instance.
        Otherwise, treat it as a URL and try to fetch the content. If successful, the raw retrieved bytes will be
        returned.

        :param value: the filepath on the local filesystem or a URL.
        """
        try:
            # Call the method of the super class, which will raise if it ``value`` is not a valid path.
            return pathlib.Path(super().convert(value, param, ctx))
        except click.exceptions.BadParameter:
            with attempt(f'attempting to download data from `{value}`...'):
                response = requests.get(value)
                response.raise_for_status()
                return response
