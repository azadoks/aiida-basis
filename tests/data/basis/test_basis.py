# -*- coding: utf-8 -*-
"""Tests for the :py:mod:`~aiida_basis.data.basis.basis` module."""
import io

import pytest

from aiida.common.files import md5_from_filelike
from aiida.common.exceptions import ModificationNotAllowed, StoringNotAllowed
from aiida.common.links import LinkType
from aiida.orm import CalcJobNode

from aiida_basis.data.basis import BasisData, PaoData


@pytest.mark.usefixtures('clear_db')
def test_constructor():
    """Test the constructor."""
    stream = io.BytesIO(b'basis')

    basis = BasisData(stream)
    assert isinstance(basis, BasisData)
    assert not basis.is_stored


@pytest.mark.usefixtures('clear_db')
def test_constructor_invalid():
    """Test the constructor for invalid arguments."""
    with pytest.raises(TypeError, match='missing 1 required positional argument'):
        BasisData()  # pylint: disable=no-value-for-parameter


@pytest.mark.usefixtures('clear_db')
def test_store():
    """Test the `BasisData.store` method."""
    stream = io.BytesIO(b'basis')
    md5_correct = md5_from_filelike(stream)
    md5_incorrect = 'abcdef0123456789'
    stream.seek(0)

    basis = BasisData(io.BytesIO(b'basis'))

    with pytest.raises(StoringNotAllowed, match='no valid element has been defined.'):
        basis.store()

    basis.element = 'Ar'
    basis.set_attribute(BasisData._key_md5, md5_incorrect)  # pylint: disable=protected-access

    with pytest.raises(StoringNotAllowed, match=r'md5 does not match that of stored file:'):
        basis.store()

    basis.md5 = md5_correct
    result = basis.store()
    assert result is basis
    assert basis.is_stored


@pytest.mark.usefixtures('clear_db')
def test_element():
    """Test the `BasisData.element` property."""
    element = 'Ar'
    basis = BasisData(io.BytesIO(b'basis'))
    assert basis.element is None

    element = 'He'
    basis.element = element
    assert basis.element == element

    with pytest.raises(ValueError, match=r'.* is not a valid element'):
        basis.element = 'Aa'

    basis.store()

    with pytest.raises(ModificationNotAllowed, match='the attributes of a stored entity are immutable'):
        basis.element = element


@pytest.mark.usefixtures('clear_db')
def test_md5():
    """Test the `BasisData.md5` property."""
    stream = io.BytesIO(b'basis')
    md5 = md5_from_filelike(stream)
    stream.seek(0)

    basis = BasisData(stream)
    basis.element = 'Ar'
    assert basis.md5 == md5

    with pytest.raises(ValueError, match=r'md5 does not match that of stored file.*'):
        basis.md5 = 'abcdef0123456789'

    basis.store()

    with pytest.raises(ModificationNotAllowed, match='the attributes of a stored entity are immutable'):
        basis.md5 = md5


@pytest.mark.usefixtures('clear_db')
def test_store_indirect():
    """Test the `BasisData.store` method when called indirectly because its is an input."""
    basis = BasisData(io.BytesIO(b'basis'))
    basis.element = 'Ar'

    node = CalcJobNode()
    node.add_incoming(basis, link_type=LinkType.INPUT_CALC, link_label='basis')
    node.store_all()


@pytest.mark.usefixtures('clear_db')
def test_get_or_create(get_basis_data):
    """Test the ``BasisData.get_or_create`` classmethod."""
    pao = get_basis_data(entry_point='pao')
    stream = io.BytesIO(pao.get_content().encode('utf-8'))

    original = BasisData.get_or_create(stream)
    original.element = pao.element
    assert isinstance(original, BasisData)
    assert not original.is_stored

    # Need to store it so it can actually be loaded from it by the ``get_or_create`` method
    original.store()

    # Return the stream to initial state and call again, which should return the same node.
    stream.seek(0)
    duplicate = BasisData.get_or_create(stream)
    assert isinstance(duplicate, BasisData)
    assert duplicate.is_stored
    assert duplicate.uuid == original.uuid

    # If the content is different, we should get a different node.
    stream.seek(0)
    different_content = BasisData.get_or_create(io.BytesIO(b'different'))
    different_content.element = pao.element
    assert isinstance(different_content, BasisData)
    assert not different_content.is_stored
    assert different_content.uuid != original.uuid

    # If the class is different, even if it is a subclass, we should get a different node even if content is identical
    stream.seek(0)
    different_class = PaoData.get_or_create(stream)
    assert isinstance(different_class, BasisData)
    assert not different_class.is_stored
    assert different_class.uuid != original.uuid
