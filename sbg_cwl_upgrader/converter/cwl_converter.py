import json
import logging
import yaml
from humanfriendly.prompts import prompt_for_confirmation
from sevenbridges import NotFound

from sbg_cwl_upgrader.validator.cwl_validation import CWLValidator
from sbg_cwl_upgrader.decomposer.sbg_cwl_decomposer import (breakdown_wf_sbg,
                                                            breakdown_wf_local)
from sbg_cwl_upgrader.cwl_utils import (yaml_ext, json_ext,
                                        is_local, add_revision_note)
from sbg_cwl_upgrader.sbg_utils import init_api

import os
from termcolor import colored
from sbg_cwl_upgrader.converter.workflow import CWLWorkflowConverter
from sbg_cwl_upgrader.converter.tool import CWLToolConverter

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

logger = logging.getLogger(__name__)


def dict_to_yaml(data: dict, out_path: str):
    with open(out_path, 'w') as outfile:
        yaml.dump(data, outfile, Dumper=Dumper)


def dict_to_json(data: dict, out_path: str):
    with open(out_path, 'w') as outfile:
        json.dump(data, outfile, sort_keys=True,
                  indent=4, separators=(',', ': '))


class CWLConverterFacade:
    """
    Facade class for the CWL (tool and wf) conversion classes.
    """

    def __init__(self,
                 input_: str,
                 output: str = None,
                 token: str = None,
                 platform: str = None,
                 app_revision: str = None,
                 profile: str = 'default',
                 endpoint: str = None,
                 validate: bool = False,
                 update: bool = False,
                 decompose: bool = False):
        msg = 'Converting...'
        logger.info(msg)
        print(colored(msg, 'green'))

        # For local input, output path/app must be specified.
        if is_local(input_) and not output:
            raise Exception('Output file not specified.')

        # Initialize API and user info
        self.api = None
        self.username = None
        self.input_ = input_
        self.output = output
        self.validate = validate
        self.update = update
        self.decompose = decompose

        if not (is_local(input_) and is_local(output)):
            self.api = init_api(profile=profile, platform=platform,
                                dev_token=token, endpoint=endpoint)
            self.username = self.api.users.me().username

        self.app_revision = int(app_revision) \
            if app_revision is not None else None

        # Perform conversion
        self.data = self._parse(self._load_input_cwl())

        # region remove batch
        # Remove batch information from cwl1 version
        def remove_batch(d: dict):
            if 'class' in d and d['class'] == 'Workflow':
                d.pop('sbg:batchInput', None)
                d.pop('sbg:batchBy', None)
                if 'inputs' in d:
                    for i in d['inputs']:
                        i.pop('batchType', None)
                if 'steps' in d:
                    for step in d['steps']:
                        if 'run' in step:
                            remove_batch(step['run'])

        remove_batch(self.data)
        # endregion

        msg = ("Please check javascript expressions and globs "
               "in your wrapper. Errors are possible due to "
               "unsupported backward compatibility.")
        print(colored(msg, 'yellow'))

        # Validate JS expressions for ES5.1 strict-mode syntax
        if validate:
            CWLValidator().validate(self.data)

        msg = 'Converting done.'
        logger.info(msg)
        print(colored(msg, 'green'))

        # Add contribution info
        if output and not is_local(output):
            slash_count = output.count('/')
            if slash_count > 2:
                raise Exception('App id can\'t have more than 2 \'/\'.')
            elif slash_count == 2:
                full_id = output
            elif slash_count == 1:
                full_id = self.username + '/' + output
            else:
                split = input_.split('/')
                full_id = '/'.join([split[0], split[1], output])
            self.data['sbg:createdBy'] = self.username
            self.data['sbg:contributors'] = [self.username]
            self.data['sbg:project'] = '/'.join([self.username,
                                                 full_id.split('/')[1]])
        else:
            if not is_local(input_):
                full_id = input_
            else:
                full_id = None

            if (self.username and 'sbg:contributors' in self.data
                    and self.username not in self.data['sbg:contributors']
                    and isinstance(self.data['sbg:contributors'], list)):
                self.data['sbg:contributors'].append(self.username)

        if full_id:
            self.data['sbg:id'] = self.data['id'] = full_id

        # Create output
        if is_local(output):
            # Dump output to file
            if output.endswith(tuple(yaml_ext())):
                dict_to_yaml(self.data, output)
            elif output.endswith(tuple(json_ext())):
                dict_to_json(self.data, output)
            # Decompose workflow
            if self.data['class'] == 'Workflow':
                if not decompose:
                    decompose = prompt_for_confirmation(
                        'Do you want to also install '
                        'all tools and subworkflows from this workflow?',
                        default=True)
                if decompose:
                    breakdown_wf_local(wf_path=output)
        else:
            # Add revision note
            rev_note = 'Upgraded to {} from {}'.format(
                self.data['cwlVersion'],
                input_
            )
            if 'sbg:revision' in self.data:
                rev_note += ', revision {}'.format(self.data['sbg:revision'])
            data = add_revision_note(self.data, rev_note)

            # Install converted app
            try:  # Check if app exists and create new revision
                old_rev = self.api.apps.get(full_id, api=self.api)
                if not update:
                    update = prompt_for_confirmation(
                        'Do you want to update app with id: \'' +
                        full_id + '\'' + '?', default=True)
                if update:
                    self.api.apps.create_revision(
                        full_id, old_rev.revision + 1, data, api=self.api)
                    msg = ("New revision has just been created.\nID: " +
                           full_id +
                           "\nrevision: " +
                           str(old_rev.revision + 1))
                    print(colored(msg, 'green'))
                    logger.info(msg)
            except NotFound:  # Install if app does not exist
                if not update:
                    update = prompt_for_confirmation(
                        'Do you want to install app with id: \'' +
                        full_id + '\'' + '?', default=True)
                if update:
                    self.api.apps.install_app(full_id, data, api=self.api)
                    msg = ("Application has just been installed.\nID: " +
                           full_id + "\nrevision: 0")
                    print(colored(msg, 'green'))
                    logger.info(msg)
            # Decompose and install parts if it's an installed/updated workflow
            if update and data['class'] == 'Workflow':
                if not decompose:
                    decompose = prompt_for_confirmation(
                        'Do you want to also install'
                        ' all tools and subworkflows from this workflow?',
                        default=True)
                if decompose:
                    breakdown_wf_sbg(wf_name=full_id.split('/')[2],
                                     project_id='/'.join(
                                         full_id.split('/')[:2]),
                                     wf_json=data,
                                     api=self.api)

    def _load_input_cwl(self):
        """
        Load input raw CWL object from local or platform input.
        """
        if is_local(self.input_):
            if os.path.exists(self.input_):
                with open(self.input_, 'r') as f:
                    if self.input_.endswith(tuple(yaml_ext())):
                        raw = yaml.load(f, Loader=Loader)
                    else:
                        raw = json.load(f)
            else:
                raise Exception('File {} not found.' % self.input_)
        else:
            if not isinstance(self.app_revision, int):
                app = self.api.apps.get(self.input_)
            else:
                app = self.api.apps.get_revision(id=self.input_,
                                                 revision=self.app_revision)
            raw = app.raw

        # Exit is input is not sbg:draft-2
        if raw["cwlVersion"] != "sbg:draft-2":
            print(colored("Input CWL is not sbg:draft-2", "red"))
            exit(1)

        return raw

    @staticmethod
    def _parse(data):
        if 'class' in data and isinstance(data['class'], str):
            if data['class'] == 'CommandLineTool':
                return CWLToolConverter().convert_dict(data)
            elif data['class'] == 'Workflow':
                return CWLWorkflowConverter().convert_dict(data)
        else:
            raise ValueError('Invalid cwl class.')
