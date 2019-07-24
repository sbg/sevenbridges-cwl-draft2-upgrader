import sevenbridges as sbg
import logging
from termcolor import colored
from sevenbridges import App
from sevenbridges.errors import NotFound, Unauthorized, Forbidden
from sbg_cwl_upgrader.cwl_utils import add_revision_note, calc_json_hash

logger = logging.getLogger(__name__)


def replace_special_characters(string: str):
    """Replace special characters in step id with -"""
    parts = []
    for word in string.split(' '):
        part = ''
        for c in word:
            if c.isalnum():
                part += c
            elif part:
                parts.append(part)
                part = ''
        if part:
            parts.append(part)
    return '-'.join(parts)


def install_or_upgrade_app(step_id: str,
                           project_id: str,
                           raw_json: dict,
                           api: sbg.Api):
    """Update the app if it exists, install it if not"""

    # Replace special characters in step id with -
    step_id = replace_special_characters(step_id)

    app_query = api.apps.query(id='{}/{}'.format(project_id, step_id))
    if len(app_query):
        app = app_query[0]
        api.apps.create_revision(app.id,
                                 app.revision + 1,
                                 raw_json,
                                 api=api)
    else:
        App.install_app('{}/{}'.format(project_id, step_id), raw_json, api=api)

    return api.apps.get('{}/{}'.format(project_id, step_id))


def add_include_in_ports(step_json: dict, included_ids: list):
    """Add sbg:includeInPorts key to d2 apps for inputs included in ports"""
    if step_json['cwlVersion'] == 'sbg:draft-2':
        for j, inp in enumerate(step_json['inputs']):
            if inp['id'] in included_ids:
                step_json['inputs'][j]['sbg:includeInPorts'] = True
    return step_json


def step_cleanup(app_raw: dict):
    """Clean up step json from junk"""

    junk_keys = ['label',
                 'x',
                 'y',
                 'appUrl',
                 'sbg:contributors',
                 'sbg:revisionNotes']

    for junk_key in junk_keys:
        app_raw.pop(junk_key, None)
    return app_raw


def breakdown_wf_sbg(wf_name: str,
                     project_id: str,
                     wf_json: dict,
                     api: sbg.Api,
                     installed_apps: dict = None):
    """
    Go through all the steps (tools and nested workflows).
    Install them in the project.
    Link them to the main workflow.
    Update the main workflow.
    :param wf_name: Workflow name
    :param project_id: SBG Project ID
    :param wf_json: Workflow JSON dict
    :param api: Sevenbridges API initialized
    :param installed_apps: dict with already installed apps
    :return: (updated_wf: sevenbridges.App, installed_apps: dict)
    """

    msg = ("Decomposing workflow with ID '{}'"
           " and installing individual parts. "
           "This may take a minute or two.\n"
           "Set log level to INFO "
           "to track decomposing progress.").format(project_id + '/' + wf_name)
    logger.info(msg)
    print(colored(msg, 'green'))

    installed_apps = installed_apps or dict()

    for idx, step in enumerate(wf_json['steps']):
        app_raw_dict = step['run']  # Raw app

        # Temporarily remove app name from json
        label_flag = False
        if 'label' in app_raw_dict:
            try:
                wf_app_label = api.apps.get(
                    app_raw_dict['sbg:id']
                ).raw['label']
            except (KeyError, NotFound, Unauthorized, Forbidden):
                wf_app_label = app_raw_dict['label']
            label_flag = True

        # Get old app id info
        old_app_id = app_raw_dict.get('sbg:id', 'External app')

        # Remove label, x and y keys from 'run' in sbg workflow if they exist
        app_raw_dict = step_cleanup(app_raw_dict)

        # Remove sbg:includeInPorts key and required:False in sbg:draft2 app
        included_ports = []
        if (app_raw_dict['cwlVersion'] == 'sbg:draft-2' and
           app_raw_dict['class'] == 'CommandLineTool'):
            for inp_no, inp in enumerate(app_raw_dict['inputs']):
                if 'sbg:includeInPorts' in inp:
                    included_ports.append(inp['id'])
                    del app_raw_dict['inputs'][inp_no]['sbg:includeInPorts']
                if 'required' in inp and not inp['required']:
                    del app_raw_dict['inputs'][inp_no]['required']

        # Check if app is already installed and use existing app.
        # Avoids making duplicate apps.
        app_hash = calc_json_hash(app_raw_dict)
        if app_hash in installed_apps:
            installed_app = installed_apps[app_hash]

            logger.info('Working on ' + step['id'] + '\n')

            step_json = dict(installed_app.raw)
            if label_flag:
                step_json['label'] = wf_app_label

            wf_json['steps'][idx]['run'] = add_include_in_ports(step_json,
                                                                included_ports)

            logger.info('Using installed app ' + step_json['sbg:id'] + '\n')
        else:  # Install the app in the workflow
            # Get app name from original app
            if label_flag:  # For sbg apps use platform name
                app_raw_dict['label'] = wf_app_label

            # For single tools install them and link them to the workflow.
            if app_raw_dict['class'] in ('CommandLineTool', 'ExpressionTool'):

                logger.info('Working on ' + step['id'] + '\n')

                new_app = install_or_upgrade_app(step['id'].lstrip('#'),
                                                 project_id, app_raw_dict, api)
                if label_flag:
                    del app_raw_dict['label']
                app_hash = calc_json_hash(app_raw_dict)
                installed_apps[app_hash] = new_app

                logger.info('Installing ' + new_app.raw['sbg:id'] +
                            ' - replacing ' + old_app_id + '\n')
                new_app_json = new_app.raw
                if label_flag:
                    new_app_json['label'] = wf_app_label
                wf_json['steps'][idx]['run'] = add_include_in_ports(
                    new_app_json, included_ports)

            # For nested wfs: install all tools,
            # install nested workflow,
            # link to the main workflow.
            elif app_raw_dict['class'] == 'Workflow':
                logger.info('\nWorking on nested workflow ' +
                            step['id'] + ':\n')
                new_app, installed_apps = breakdown_wf_sbg(
                    step['id'].lstrip('#'),
                    project_id,
                    app_raw_dict,
                    api,
                    installed_apps
                )
                if label_flag:
                    del app_raw_dict['label']
                app_hash = calc_json_hash(app_raw_dict)
                installed_apps[app_hash] = new_app

                logger.info('\nInserting nested workflow ' +
                            new_app.raw['sbg:id'] +
                            ' - replacing ' + old_app_id + '\n\n')

                new_app_json = new_app.raw
                if label_flag:
                    new_app_json['label'] = wf_app_label
                wf_json['steps'][idx]['run'] = add_include_in_ports(
                    new_app_json, included_ports)

    msg = ("Rewiring done. "
           "New tools are now connected"
           " in the {}/{} workflow").format(project_id, wf_name)
    logger.info(msg)
    print(colored(msg, 'green'))

    # Try to find the nested workflow in already installed apps.
    wf_hash = calc_json_hash(wf_json)
    if wf_hash in installed_apps:
        return installed_apps[wf_hash], installed_apps

    # Update the workflow with modified json linked to new tools.
    updated_wf = install_or_upgrade_app(
        wf_name, project_id,
        add_revision_note(wf_json, 'Workflow decomposed'), api
    )

    # Add nested workflow to installed_apps
    installed_apps[wf_hash] = updated_wf

    logger.info('\nSuccessfully updated ' + updated_wf.raw['sbg:id'] + '\n')
    return updated_wf, installed_apps
