# -*- coding: utf-8 -*-
"""Command line interface utilities."""
from contextlib import contextmanager

from aiida.cmdline.utils import echo

__all__ = ('attempt', 'create_basis_set_from_directory', 'create_basis_set_from_archive')


@contextmanager
def attempt(message, exception_types=Exception, include_traceback=False):
    """Context manager to be used to wrap statements in CLI that can throw exceptions.

    :param message: the message to print before yielding
    :param include_traceback: boolean, if True, will also print traceback if an exception is caught
    """
    import sys
    import traceback

    echo.echo_info(message, nl=False)

    try:
        yield
    except exception_types as exception:  # pylint: disable=broad-except
        echo.echo_highlight(' [FAILED]', color='error', bold=True)
        message = str(exception)
        if include_traceback:
            message += f"\n{''.join(traceback.format_exception(*sys.exc_info()))}"
        echo.echo_critical(message)
    else:
        echo.echo_highlight(' [OK]', color='success', bold=True)


def create_basis_set_from_directory(cls, label, dirpath, basis_type=None):
    """Construct a new basis set instance from a directory.
    
    .. warning:: the directory should not contain any subdirectories, just the basis files.

    :param cls: the basis set class to use, e.g. ``OpenmxBasisSet``
    :param label: the label for the new basis set.
    :param dirpath: absolute path to the directory holding the basis files.
    :param basis_type: subclass of ``BasisData`` to be used for the parsed bases. If not specified and
        the basis set only defines a single supported basis type in ``_basis_types`` then that will be used otherwise
        a ``ValueError`` is raised.
    :return: newly created basis set.
    :raises OSError: if the bases could not be parsed into a basis set.
    """
    try:
        basis_set = cls.create_from_folder(dirpath, label, pseudo_type=basis_type)
    except ValueError as exception:
        raise OSError(f'failed to parse bases from `{dirpath}`: {exception}') from exception

    return basis_set


def create_basis_set_from_archive(cls, label, filepath_archive, fmt=None, basis_type=None):
    """Construct a new basis set instance from a tar.gz archive.

    .. warning:: the archive should not contain any subdirectories, but just the basis files.

    :param cls: the basis set class to use, e.g. ``OpenmxBasisSet``
    :param label: the label for the new basis set
    :param filepath_archive: absolute filepath to the .tar.gz archive containing the basis set
    :param fmt: the format of the archive, if not specified will attempt to guess based on extension of ``filepath``
    :param basis_type: subclass of ``BasisData`` to be used for the parsed bases. If not specified and
        the basis set only defines a single supported basis type in ``_basis_types`` then that will be used otherwise
        a ``ValueError`` is raised.
    :return: newly created basis set
    :raises OSError: if the archive could not be unpacked or bases in it could not be parsed into a basis set
    """
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory() as dirpath:

        try:
            shutil.unpack_archive(filepath_archive, dirpath, format=fmt)
        except shutil.ReadError as exception:
            raise OSError(f'failed to unpack the archive `{filepath_archive}`: {exception}') from exception

        basis_set = create_basis_set_from_directory(cls, label, dirpath, basis_type)

    return basis_set
