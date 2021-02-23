# -*- coding: utf-8 -*-
"""Command to install a basis set."""
from aiida_basis.cli.utils import create_basis_set_from_directory
import json
import os
import shutil
import tempfile

import click

from aiida.cmdline.utils import decorators, echo
from aiida.cmdline.params import options as options_core
from aiida.cmdline.params import types

from .params import options
from .root import cmd_root


@cmd_root.group('install')
def cmd_install():
    """Install basis sets."""


@cmd_install.command('basisset')
@click.argument('archive', type=types.FileOrUrl(mode='rb'))
@click.argument('label', type=click.STRING)
@options_core.DESCRIPTION(help='Description for the basis set.')
@options.ARCHIVE_FORMAT()
@options.FAMILY_TYPE()
@options.TRACEBACK()
@decorators.with_dbenv()
def cmd_install_basis_set(archive, label, description, archive_format, basis_set_type, traceback):  # pylint: disable=too-many-arguments
    """Install a standard basis set from an ARCHIVE on the local file system or from a URL.

    The command will attempt to infer the archive format from the filename extension of the ARCHIVE. If this fails, the
    archive format can be specified explicitly with the archive format option, which will also display which formats
    are supported.

    By default, the command will create a base `PseudoPotentialFamily`, but the type can be changed with the family
    type option. If the base type is used, the pseudo potential files in the archive *have* to have filenames that
    strictly follow the format `ELEMENT.EXTENSION`, because otherwise the element cannot be determined automatically.
    """
    from .utils import attempt, create_basis_set_from_archive

    # The `archive` is now either a `http.client.HTTPResponse` or a normal filelike object, so we get the original file
    # name in a different way.
    try:
        suffix = os.path.basename(archive.url)
    except AttributeError:
        suffix = os.path.basename(archive.name)

    # Write the content of the archive to a temporary file, because `create_family_from_archive` does currently not
    # accept filelike objects because the underlying `shutil.unpack_archive` does not. Likewise, `unpack_archive` will
    # attempt to deduce the archive format from the filename extension, so it is important we maintain the original
    # filename. Of course if this fails, users can specify the archive format explicitly wiht the corresponding option.
    with tempfile.NamedTemporaryFile(mode='w+b', suffix=suffix) as handle:
        shutil.copyfileobj(archive, handle)
        handle.flush()

        with attempt('unpacking archive and parsing pseudos... ', include_traceback=traceback):
            basis_set = create_basis_set_from_archive(basis_set_type, label, handle.name, fmt=archive_format)

    basis_set.description = description
    echo.echo_success(f'installed `{label}` containing {basis_set.count()} elements')


@cmd_install.command('openmx')
@options.VERSION(type=click.Choice(['13', '19']), default='19', show_default=True)
@options.PROTOCOL(type=click.Choice(['quick', 'standard', 'precise']), default='standard', show_default=True)
@options.HARDNESS(type=click.Choics(['soft', 'hard']), default='soft', show_default=True)
@options.TRACEBACK()
@decorators.with_dbenv()
def cmd_install_sssp(version, protocol, hardness, traceback):
    """Install an OpenMX configuration.

    The OpenMX configuration will be automatically downloaded from t-ozaki.issp.u-tokyo.ac.jp to create a new
    `OpenmxBasisSet`.
    """
    # pylint: disable=too-many-locals
    import requests

    from aiida.common.files import md5_file
    from aiida.orm import Group, QueryBuilder

    from aiida_basis import __version__
    from aiida_basis.groups.set.openmx import OpenmxConfiguration, OpenmxBasisSet
    from .utils import attempt, create_basis_set_from_archive

    configuration = OpenmxConfiguration(version, protocol, hardness)
    label = OpenmxBasisSet.format_configuration_label(configuration)
    description = f'OpenMX 20{version} {hardness} {protocol} installed with aiida-basis v{__version__}'

    if configuration not in OpenmxBasisSet.valid_configurations:
        echo.echo_critical(f'{version} {hardness} {protocol} is not a valid OpenMX basis set configuration')

    if QueryBuilder.append(OpenmxBasisSet, filters={'label': label}).first():
        echo.echo_critical(f'{OpenmxBasisSet.__name__}<{label}> is already installed')

    with tempfile.TemporaryDirectory() as dirpath:
        urls = OpenmxBasisSet.get_urls_configuration(configuration)
        with attempt('downloading selected basis set files... ', include_traceback=traceback):
            for url in urls:
                response = requests.get(url)
                response.raise_for_status()
        
        with attempt('parsing PAOs... ', include_traceback=traceback):
            basis_set = create_basis_set_from_directory(OpenmxBasisSet, label, dirpath)

        # TODO: check md5 against metadata
        # TODO: add recommended orbital configurations from metadata


        basis_set.description = description
        basis_set.set_or




        cutoffs = {}

        for element, values in metadata.items():
            if family.get_pseudo(element).md5 != values['md5']:
                Group.objects.delete(family.pk)
                msg = f"md5 of pseudo for element {element} does not match that of the metadata {values['md5']}"
                echo.echo_critical(msg)

            # Cutoffs are in Rydberg but need to be stored in the family in electronvolt.
            cutoffs[element] = {
                'cutoff_wfc': values['cutoff_wfc'] * units.RY_TO_EV,
                'cutoff_rho': values['cutoff_rho'] * units.RY_TO_EV,
            }

        family.description = description
        family.set_cutoffs({'normal': cutoffs})

        echo.echo_success(f'installed `{label}` containing {family.count()} pseudo potentials')
