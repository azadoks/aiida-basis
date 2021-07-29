# -*- coding: utf-8 -*-
"""Tests for the :mod:`~aiida_basis.cli.params.types` module."""
import click
import pytest

from aiida_basis.cli.params import types
from aiida_basis.groups.set import BasisSet


def test_basis_set_type_param_convert(ctx):
    """Test the `BasisSetTypeParam.convert` method."""
    param = types.BasisSetTypeParam()

    with pytest.raises(click.BadParameter, match=r'.*is not an existing group plugin.'):
        param.convert('non.existing', None, ctx)

    with pytest.raises(click.BadParameter, match=r'.*entry point is not a subclass of `BasisSet`.'):
        param.convert('core', None, ctx)

    assert param.convert('basis.set', None, ctx) is BasisSet


def test_basis_set_type_param_complete(ctx):
    """Test the `BasisSetTypeParam.complete` method."""
    param = types.BasisSetTypeParam()
    assert isinstance(param.complete(ctx, ''), list)
    assert isinstance(param.complete(ctx, 'basis'), list)
    assert ('basis.set', '') in param.complete(ctx, 'basis')
