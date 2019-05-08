# -*- coding: utf-8 -*-
"""
Command line scripts to launch a `Pw2wannier90Calculation` for testing and demonstration purposes.

This launcher assumes that the SEED and the PREFIX used in the previous PW calculation (parent_folder)
are the same as those hardcoded in the Pw2wannier90Calculation class.
We also hardcode some parameters and options.
"""
from __future__ import absolute_import
import click

from aiida.cmdline.params import options, types
from aiida.cmdline.params.options import OverridableOption
from aiida.cmdline.utils import decorators

from aiida_quantumespresso.cli.utils import options as options_qe

PARENT_FOLDER = OverridableOption(
    '-F',
    '--parent_folder',
    'parent_folder',
    metavar='RemoteData/FolderData',  # placeholder in the help text
    type=types.NodeParamType(sub_classes=('aiida.data:remote', 'aiida.data:folder')),
    help='A RemoteData or FolderData node identified by its ID or UUID.')

SINGLE_FILE = OverridableOption(
    '-S',
    '--single_file',
    'single_file',
    metavar='SinglefileData',  # placeholder in the help text
    type=types.NodeParamType(sub_classes=('aiida.data:singlefile',)),
    help='A SinglefileData node identified by its ID or UUID.')


@click.command()
@options.CODE(required=True, type=types.CodeParamType(entry_point='quantumespresso.pw2wannier90'))
@PARENT_FOLDER(required=True, help='RemoteData folder containing the output of a PW calculation')
@SINGLE_FILE(required=True, help='SinglefileData containing the .nnkp file generated by a wannier90.x preprocessing')
@options_qe.MAX_NUM_MACHINES()
@options_qe.MAX_WALLCLOCK_SECONDS()
@options_qe.WITH_MPI()
@options_qe.DAEMON()
@decorators.with_dbenv()
def cli(code, parent_folder, single_file, max_num_machines, max_wallclock_seconds, with_mpi, daemon):
    """Run a Pw2wannier90Calculation with some sample parameters and the provided inputs."""
    from aiida.engine import launch
    from aiida.orm import Dict
    from aiida.plugins import CalculationFactory
    from aiida_quantumespresso.utils.resources import get_default_options

    Pw2wannier90Calculation = CalculationFactory('quantumespresso.pw2wannier90')  # pylint: disable=invalid-name

    parameters = {
        'inputpp': {
            'write_amn': True,
            'write_mmn': True,
            'write_unk': False,
            'scdm_proj': True,
            'scdm_entanglement': 'isolated',
        }
    }

    settings = {'ADDITIONAL_RETRIEVE_LIST': ['*.amn', '*.mmn', '*.eig']}

    inputs = {
        'code': code,
        'parent_folder': parent_folder,
        'nnkp_file': single_file,
        'parameters': Dict(dict=parameters),
        'settings': Dict(dict=settings),
        'metadata': {
            'options': get_default_options(max_num_machines, max_wallclock_seconds, with_mpi),
        }
    }

    if daemon:
        new_calc = launch.submit(Pw2wannier90Calculation, **inputs)
        click.echo('Submitted {}<{}> to the daemon'.format(Pw2wannier90Calculation.__name__, new_calc.pk))
    else:
        click.echo('Running a pw2wannier90.x calculation from parent {}<{}>... '.format(
            parent_folder.__class__.__name__, parent_folder.pk))
        _, new_calc = launch.run_get_node(Pw2wannier90Calculation, **inputs)
        click.echo('Pw2wannier90Calculation<{}> terminated with state: {}'.format(new_calc.pk, new_calc.process_state))
        click.echo('\n{link:25s} {node}'.format(link='Output link', node='Node pk and type'))
        click.echo('{s}'.format(s='-' * 60))
        for triple in sorted(new_calc.get_outgoing().all(), key=lambda triple: triple.link_label):
            click.echo('{:25s} {}<{}> '.format(triple.link_label, triple.node.__class__.__name__, triple.node.pk))
