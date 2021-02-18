# -*- coding: utf-8 -*-
"""Subclass of ``Group`` that serves as a base class for representing basis sets."""
import os
import re
from typing import Union, List, Tuple, Mapping

from aiida.common import exceptions
from aiida.common.lang import classproperty, type_check
from aiida.orm import Group, QueryBuilder
from aiida.plugins import DataFactory

from aiida_basis.data.basis import BasisData

__all__ = ('BasisSet',)

StructureData = DataFactory('structure')


class BasisSet(Group):
    """Group to represent a basis set.
    This is a base class that provides most of the functionality but does not actually define what type of basis
    can be contained. If ``_basis_types`` is not defined, any basis type is accepted in this
    basis set, as long as it is a subclass of ``BasisData``. Subclasses can limit which basis types can be
    hosted by setting ``_basis_types`` to a tuple of ``BasisData`` subclasses.
    """

    _key_basis_type = '_basis_type'
    _basis_types = (BasisData,)
    _bases = None

    def __repr__(self):
        """Represent the instance for debugging purposes."""
        return f'{self.__class__.__name__}<{self.pk or self.uuid}>'

    def __str__(self):
        """Represent the instance for human-readable purposes."""
        return f'{self.__class__.__name__}<{self.label}>'

    def __init__(self, *args, **kwargs):
        """Validate that the ``_basis_types`` class attribute is a tuple of ``BasisData`` subclasses."""
        if not self._basis_types or not isinstance(self._basis_types, tuple) or any(
            not issubclass(basis_type, BasisData) for basis_type in self._basis_types
        ):
            raise RuntimeError('`_basis_types` should be a tuple of `BasisData` subclasses.')

        super().__init__(*args, **kwargs)

    @classproperty
    def basis_types(cls):  # pylint: disable=no-self-argument
        """Return the basis types that this basis set accepts.
        :return: the tuple of subclasses of ``BasisData`` that this basis set can host nodes of. If it returns
            ``None``, that means all subclasses are supported.
        """
        return cls._basis_types

    @classmethod
    def _validate_basis_type(cls, basis_type):
        """Validate the ``basis_type`` passed to ``parse_bases_from_directory``.
        :return: the basis type to be used.
        """
        if basis_type is None and len(cls._basis_types) > 1:
            raise ValueError(f'`{cls}` supports more than one type, so `basis_type` needs to be explicitly passed.')

        basis_type = basis_type or cls._basis_types[0]

        if all(not issubclass(basis_type, supported_type) for supported_type in cls._basis_types):
            raise ValueError(f'`{basis_type}` is not supported by `{cls}`.')

        return basis_type

    @classmethod
    def _validate_dirpath(cls, dirpath):
        """Validate the ``dirpath`` passed to ``parse_bases_from_directory``.
        :return: the directory path to be used.
        """
        if not os.path.isdir(dirpath):
            raise ValueError(f'`{dirpath}` is not a directory')

        dirpath_contents = os.listdir(dirpath)

        if len(dirpath_contents) == 1 and os.path.isdir(os.path.join(dirpath, dirpath_contents[0])):
            dirpath = os.path.join(dirpath, dirpath_contents[0])

        return dirpath

    @classmethod
    def parse_bases_from_directory(cls, dirpath, basis_type=None, deduplicate=True):
        """Parse the basis files in the given directory into a list of data nodes.
        .. note:: The directory pointed to by `dirpath` should only contain basis files. Optionally, it can
            contain just a single directory, that contains all the basis files. If any other files are stored
            in the basepath or the subdirectory, that cannot be successfully parsed as basis files the method
            will raise a ``ValueError``.
        :param dirpath: absolute path to a directory containing bases.
        :param basis_type: subclass of ``BasisData`` to be used for the parsed bases. If not specified and
            the basis set only defines a single supported basis type in ``_basis_types`` then that will be used otherwise
            a ``ValueError`` is raised.
        :param deduplicate: if True, will scan database for existing bases of same type and with the same
            md5 checksum, and use that instead of the parsed one.
        :return: list of data nodes
        :raises ValueError: if ``dirpath`` is not a directory or contains anything other than files.
        :raises ValueError: if ``dirpath`` contains multiple bases for the same element.
        :raises ValueError: if ``basis_type`` is explicitly specified and is not supported by this basis set class.
        :raises ValueError: if ``basis_type`` is not specified and the class supports more than one basis type.
        :raises ParsingError: if the constructor of the basis type fails for one of the files in the ``dirpath``.
        """
        from aiida.common.exceptions import ParsingError

        bases = []
        dirpath = cls._validate_dirpath(dirpath)
        basis_type = cls._validate_basis_type(basis_type)

        for filename in os.listdir(dirpath):
            filepath = os.path.join(dirpath, filename)

            if not os.path.isfile(filepath):
                raise ValueError(f'dirpath `{dirpath}` contains at least one entry that is not a file')

            with open(filepath, 'rb') as handle:
                try:
                    if deduplicate:
                        basis = basis_type.get_or_create(handle, filename=filename)
                    else:
                        basis = basis_type(handle, filename=filename)
                except ParsingError as exception:
                    raise ParsingError(f'failed to parse `{filepath}`: {exception}') from exception

            if basis.element is None:
                match = re.search(r'^([A-Za-z]{1,2})\.\w+', filename)
                if match is None:
                    raise ParsingError(
                        f'`{basis.__class__}` constructor did not define the element and could not parse a valid '
                        'element symbol from the filename `{filename}` either. It should have the format '
                        '`ELEMENT.EXTENSION`'
                    )
                basis.element = match.group(1)
            bases.append(basis)

        if not bases:
            raise ValueError(f'no bases were parsed from `{dirpath}`')

        elements = set(basis.element for basis in bases)

        if len(bases) != len(elements):
            raise ValueError(f'directory `{dirpath}` contains bases with duplicate elements')

        return bases

    @classmethod
    def create_from_folder(cls, dirpath, label, *, description='', basis_type=None, deduplicate=True):
        """Create a new ``BasisSet`` from the bases contained in a directory.
        :param dirpath: absolute path to the folder containing the UPF files.
        :param label: label to give to the ``BasisSet``, should not already exist.
        :param description: description to give to the basis set.
        :param basis_type: subclass of ``BasisData`` to be used for the parsed bases. If not specified and
            the basis set only defines a single supported basis type in ``_basis_types`` then that will be used otherwise
            a ``ValueError`` is raised.
        :param deduplicate: if True, will scan database for existing bases of same type and with the same
            md5 checksum, and use that instead of the parsed one.
        :raises ValueError: if a ``BasisSet`` already exists with the given name.
        :raises ValueError: if ``dirpath`` is not a directory or contains anything other than files.
        :raises ValueError: if ``dirpath`` contains multiple bases for the same element.
        :raises ValueError: if ``basis_type`` is explicitly specified and is not supported by this basis set class.
        :raises ValueError: if ``basis_type`` is not specified and the class supports more than one basis type.
        :raises ParsingError: if the constructor of the basis type fails for one of the files in the ``dirpath``.
        """
        type_check(description, str, allow_none=True)

        try:
            cls.objects.get(label=label)
        except exceptions.NotExistent:
            basis_set = cls(label=label, description=description)
        else:
            raise ValueError(f'the {cls.__name__} `{label}` already exists')

        bases = cls.parse_bases_from_directory(dirpath, basis_type, deduplicate=deduplicate)

        # Only store the ``Group`` and the basis nodes now, such that we don't have to worry about the clean up in the
        # case that an exception is raised during creating them.
        basis_set.store()
        basis_set.add_nodes([basis.store() for basis in bases])

        return basis_set

    @property
    def basis_type(self):
        """Return the type of the bases that are hosted by this basis set.
        :return: the basis type or ``None`` if none has been set yet.
        """
        return self.get_extra(self._key_basis_type, None)

    def update_basis_type(self):
        """Update the basis type, stored as an extra, based on the current nodes in the basis set."""
        basis_types = {basis.__class__ for basis in self.bases.values()}

        if basis_types:
            assert len(basis_types) == 1, 'Basis set contains basis data nodes of various types.'
            entry_point_name = tuple(basis_types)[0].get_entry_point_name()
        else:
            entry_point_name = None

        self.set_extra(self._key_basis_type, entry_point_name)

    def add_nodes(self, nodes):
        """Add a node or a set of nodes to the basis set.
        .. note: Each basis set instance can only contain a single basis for each element.
        :param nodes: a single or list of ``Node`` instances of type that is in ``BasisSet._basis_types``.
        :raises ModificationNotAllowed: if the basis set is not stored.
        :raises TypeError: if nodes are not an instance or list of instance of any of the classes listed by
            ``BasisSet._basis_types``.
        :raises ValueError: if any of the nodes are not stored or their elements already exist in this basis set.
        """
        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot add nodes to an unstored group')

        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]

        if any(not isinstance(node, self._basis_types) for node in nodes):
            raise TypeError(f'only nodes of types `{self._basis_types}` can be added: {nodes}')

        bases = {}

        # Check for duplicates before adding any basis to the internal cache
        for basis in nodes:
            if basis.element in self.elements:
                raise ValueError(f'element `{basis.element}` already present in this basis set')
            bases[basis.element] = basis

        self.bases.update(bases)
        self.update_basis_type()

        super().add_nodes(nodes)

    def remove_nodes(self, nodes):
        """Remove a basis or a set of bases from the basis set.
        :param nodes: a single or list of ``BasisData`` instances or subclasses thereof.
        """
        super().remove_nodes(nodes)

        if not isinstance(nodes, (list, tuple)):
            nodes = (nodes,)

        removed = [node.pk for node in nodes]
        self._bases = {basis.element: basis for basis in self.bases.values() if basis.pk not in removed}
        self.update_basis_type()

    def clear(self):
        """Remove all the bases from this basis set."""
        super().clear()
        self._bases = None
        self.update_basis_type()

    @property
    def bases(self):
        """Return the dictionary of bases of this basis set indexed on the element symbol.
        :return: dictionary of element symbol mapping bases
        """
        if self._bases is None:
            self._bases = {basis.element: basis for basis in self.nodes}

        return self._bases

    @property
    def elements(self):
        """Return the list of elements for which this basis set defines a basis.
        :return: list of element symbols
        """
        return list(self.bases.keys())

    def get_basis(self, element):
        """Return the basis for the given element.
        :param element: the element for which to return the corresponding basis.
        :return: basis instance if it exists
        :raises ValueError: if the basis set does not contain a basis for the given element
        """
        try:
            basis = self.bases[element]
        except KeyError:
            builder = QueryBuilder()
            builder.append(self.__class__, filters={'id': self.pk}, tag='group')
            builder.append(self._basis_types, filters={'attributes.element': element}, with_group='group')

            try:
                basis = builder.one()[0]
            except exceptions.MultipleObjectsError as exception:
                raise RuntimeError(f'basis set `{self.label}` contains multiple bases for `{element}`') from exception
            except exceptions.NotExistent as exception:
                raise ValueError(
                    f'basis set `{self.label}` does not contain basis for element `{element}`'
                ) from exception
            else:
                self.bases[element] = basis

        return basis

    def get_bases(
        self,
        *,
        elements: Union[List[str], Tuple[str]] = None,
        structure: StructureData = None,
    ) -> Mapping[str, StructureData]:
        """Return the mapping of kind names on basis data nodes for the given list of elements or structure.
        :param elements: list of element symbols.
        :param structure: the ``StructureData`` node.
        :return: dictionary mapping the kind names of a structure on the corresponding basis data nodes.
        :raises ValueError: if the basis set does not contain a basis for any of the elements of the given structure.
        """
        if elements is not None and structure is not None:
            raise ValueError('cannot specify both keyword arguments `elements` and `structure`.')

        if elements is None and structure is None:
            raise ValueError('have to specify one of the keyword arguments `elements` and `structure`.')

        if elements is not None and not isinstance(elements, (list, tuple)) and not isinstance(elements, StructureData):
            raise ValueError('elements should be a list or tuple of symbols.')

        if structure is not None and not isinstance(structure, StructureData):
            raise ValueError('structure should be a `StructureData` instance.')

        if structure is not None:
            return {kind.name: self.get_basis(kind.symbol) for kind in structure.kinds}

        return {element: self.get_basis(element) for element in elements}