# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name
"""Tests for the :py:`~aiida_basis.data.basis.pao` module."""
import io
import os
import pathlib

import pytest

from aiida.common.exceptions import ModificationNotAllowed
from aiida_basis.data.basis import PaoData
from aiida_basis.data.basis.pao import parse_z_valence


@pytest.fixture
def source(request, filepath_basis):
    """Return a basis, eiter as ``str``, ``Path`` or ``io.BytesIO``."""
    filepath = pathlib.Path(filepath_basis(entry_point='pao')) / 'Ar.pao'

    if request.param is str:
        return str(filepath)

    if request.param is pathlib.Path:
        return filepath

    return io.BytesIO(filepath.read_bytes())


@pytest.mark.parametrize('source', (io.BytesIO, str, pathlib.Path), indirect=True)
def test_constructor_source_types(source):
    """Test the constructor accept the various types."""
    basis = PaoData(source)
    assert isinstance(basis, PaoData)
    assert not basis.is_stored


def test_constructor(filepath_basis):
    """Test the constructor."""
    for filename in os.listdir(filepath_basis('pao')):
        with open(os.path.join(filepath_basis('pao'), filename), 'rb') as handle:
            basis = PaoData(handle, filename=filename)
            assert isinstance(basis, PaoData)
            assert not basis.is_stored
            assert basis.element == filename.split('.')[0]


@pytest.mark.usefixtures('clear_db')
def test_set_file(filepath_basis, get_basis_data):
    """Test the `PaoData.set_file` method.

    This method allows to change the file, as long as the node has not been stored yet. We need to verify that all the
    information, such as attributes are commensurate when it is stored.
    """
    basis = get_basis_data(element='Ar', entry_point='pao')
    assert basis.element == 'Ar'

    with open(os.path.join(filepath_basis('pao'), 'He.pao'), 'rb') as handle:
        basis.set_file(handle)
        assert basis.element == 'He'

        basis.store()
        assert basis.element == 'He'

        with pytest.raises(ModificationNotAllowed):
            basis.set_file(handle)


@pytest.mark.parametrize(
    'content', (
        'valence.electron 8.0', 'Valence.Electron  8.000', 'VALENCE.ELECTRON 8.0', 'valence.electron 8.0e1',
        'valence.electron 8.000E01'
    )
)
def test_parse_z_valence(content):
    """Test the ``parse_z_valence`` method."""
    assert parse_z_valence(content)


# FUTURE: test other PaoData-related functions
