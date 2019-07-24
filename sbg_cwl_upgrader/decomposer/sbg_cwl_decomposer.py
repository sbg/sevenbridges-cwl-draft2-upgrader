import argparse
import sys
from sbg_cwl_upgrader.sbg_utils import (add_logging_to_args,
                                        configure_logging,
                                        add_sbg_auth_to_args, init_api)
from sbg_cwl_upgrader.cwl_utils import is_local
from sbg_cwl_upgrader.decomposer.local import breakdown_wf_local
from sbg_cwl_upgrader.decomposer.remote import breakdown_wf_sbg
from sevenbridges.errors import NotFound, Unauthorized


def create_arg_parser():

    parser = argparse.ArgumentParser(
        description='Installs all apps from the workflow in the '
                    'current project and links the workflow to those apps')

    parser.add_argument('-a', '--app', action='append', required=True,
                        help='workflow app ID or local path, '
                             'can have multiple values.')

    add_logging_to_args(parser)
    add_sbg_auth_to_args(parser)
    return parser


def main(args=sys.argv[1:]):
    """
    Entrypoint and CLI for sbg_cwl_decomposer tool.
    """

    args = vars(create_arg_parser().parse_args(args))

    configure_logging(args)

    wf_id_list = args['app']

    for wf_id in wf_id_list:
        if is_local(wf_id):
            breakdown_wf_local(wf_id)
        else:
            api = init_api(profile=args['profile'],
                           platform=args['platform'],
                           dev_token=args['token'],
                           endpoint=args['endpoint'])

            project_id = '/'.join(wf_id.split('/')[:2])
            try:
                wf = api.apps.get(api=api, id=wf_id)
            except (NotFound, Unauthorized):
                raise ValueError("Wrong inputs. Workflow does not"
                                 " exist on the platform or "
                                 "your token is not correct.")
            breakdown_wf_sbg(wf_id.split('/')[2],
                             project_id,
                             wf.raw,
                             api)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
