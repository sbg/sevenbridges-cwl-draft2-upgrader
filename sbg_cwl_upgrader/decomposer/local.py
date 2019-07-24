import os
import yaml
import logging
from termcolor import colored

from sbg_cwl_upgrader.cwl_utils import (resolve_cwl,
                                        cwl_ensure_dict,
                                        calc_json_hash)

logger = logging.getLogger(__name__)


def safe_dump_yaml(tool_path: str, tool_json: dict):
    """
    Dump dict to a yaml file without overriding existing files (add _#_ prefix)
    :param tool_path: expected path
    :param tool_json: tool dict
    :return: path where file is dumped
    """
    counter = 1
    basedir = os.path.dirname(tool_path)
    basename = os.path.basename(tool_path)
    # Append and increment prefix while there is a conflict
    while os.path.exists(tool_path):
        tool_path = os.path.join(basedir, '_{}_{}'.format(counter, basename))
        counter += 1
    # Ensure any missing path directories are created
    os.makedirs(os.path.dirname(os.path.abspath(tool_path)), exist_ok=True)
    # Dump yaml to the path
    with open(tool_path, 'w') as f:
        yaml.dump(tool_json, f, default_flow_style=False)
    return tool_path


def breakdown_wf_local(wf_path: str,
                       installed_apps: dict = None,
                       nested_wf_json: dict = None,  # use if is_main is false
                       steps_dir: str = None,  # use if is_main is false
                       is_main: bool = True):
    """
    Recursively walk through all the steps (tools and nested wfs)
     and install them in steps folder.
    Reference them in the main workflow.
    :param wf_path: Path where to dump the tool/workflow
    :param installed_apps: Dict containing already installed apps.
    :param nested_wf_json: None in main call, dict in recursive calls
    :param steps_dir: None in main call, path in recursive calls
    :param is_main: True in main call, False in recursive calls
    :return: (Workflow path, Installed apps dictionary)
    """

    msg = ("Decomposing workflow '{}' and"
           " installing parts in 'steps' folder. "
           "This may take a minute or two.\n"
           "Set log level to INFO"
           " to track decomposing progress.").format(os.path.abspath(wf_path))
    logger.info(msg)
    print(colored(msg, 'green'))

    wf_path = os.path.abspath(wf_path)
    installed_apps = installed_apps or dict()
    base_dir = os.path.dirname(wf_path)
    updated_wf_path = '.'.join(wf_path.split('.')[:-1])
    if is_main:
        updated_wf_path += '_decomposed.cwl'
    else:
        updated_wf_path += '.cwl'

    # Resolve main workflow or use provided json for nested wf
    if is_main and not nested_wf_json:
        wf_json = resolve_cwl(wf_path)
    else:
        wf_json = nested_wf_json

    # Make steps dir
    steps_dir = steps_dir or os.path.join(base_dir, 'steps')
    if not os.path.exists(steps_dir):
        os.mkdir(steps_dir)

    wf_json['steps'] = cwl_ensure_dict(wf_json['steps'], 'id')
    for step_id, step in wf_json['steps'].items():
        app_hash = calc_json_hash(step['run'])
        if app_hash in installed_apps:
            wf_json['steps'][step_id]['run'] = os.path.relpath(
                installed_apps[app_hash],
                base_dir
            )
        else:
            tool_path = os.path.join(steps_dir, step_id + '.cwl')
            if step['run']['class'] in ['CommandLineTool', 'ExpressionTool']:
                # Dump run contents to file
                tool_path = safe_dump_yaml(tool_path, step['run'])
                # Add to installed apps to avoid duplicates
                installed_apps[app_hash] = os.path.abspath(tool_path)
                # Add a relative path to wf_json
                wf_json['steps'][step_id]['run'] = os.path.relpath(
                    tool_path, base_dir
                )
            elif step['run']['class'] == 'Workflow':
                nested_wf, installed_apps = breakdown_wf_local(
                        tool_path,
                        installed_apps=installed_apps,
                        nested_wf_json=step['run'],
                        is_main=False,
                        steps_dir=steps_dir
                    )
                wf_json['steps'][step_id]['run'] = os.path.relpath(
                    nested_wf,
                    base_dir
                )

    if is_main:
        with open(updated_wf_path, 'w') as f:
            yaml.dump(wf_json, f, default_flow_style=False)
        msg = ("Rewiring done. "
               "New tools are now connected"
               " in the workflow {}.").format(
            os.path.abspath(updated_wf_path))
        logger.info(msg)
        print(colored(msg, 'green'))
    else:
        wf_hash = calc_json_hash(wf_json)
        if wf_hash in installed_apps:
            return installed_apps[wf_hash], installed_apps
        else:
            safe_dump_yaml(updated_wf_path, wf_json)
            installed_apps[wf_hash] = os.path.abspath(updated_wf_path)

    return os.path.abspath(updated_wf_path), installed_apps
