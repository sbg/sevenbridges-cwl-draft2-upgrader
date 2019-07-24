import argparse
import sys
from sbg_cwl_upgrader.sbg_utils import (add_sbg_auth_to_args,
                                        configure_logging,
                                        add_logging_to_args)
from sbg_cwl_upgrader.converter.cwl_converter import CWLConverterFacade


def create_arg_parser():
    parser = argparse.ArgumentParser(
        description=' This tool converts CWL draft2 applications '
                    '(workflows, command line tools) to CWL v1.0.')

    parser.add_argument('-i', '--input', required=True,
                        help='can be either draft2 file (YAML, JSON, CWL)'
                             ' path or application ID.')
    parser.add_argument('-o', '--output', required=True,
                        help='can be either cwl v1.0 file (YAML, JSON, CWL)'
                             ' path or application ID.')
    parser.add_argument('-r', '--revision', type=int,
                        help='platform application revision. default: latest')
    parser.add_argument('-v', '--validate', action='store_true',
                        help='validate JS in the converted CWL v1.0 app.')
    parser.add_argument('-u', '--update', dest='update', action='store_true',
                        help='update/install if output is a platform app.')
    parser.add_argument('-d', '--decompose', action='store_true',
                        help='decompose the converted CWL v1.0 workflow.')

    add_logging_to_args(parser)
    add_sbg_auth_to_args(parser)

    return parser


def main(args=sys.argv[1:]):
    """
    Entrypoint and CLI for sbg_cwl_upgrader tool.
    """

    args = vars(create_arg_parser().parse_args(args))

    configure_logging(args)

    CWLConverterFacade(token=args['token'],
                       profile=args['profile'],
                       platform=args['platform'],
                       endpoint=args['endpoint'],
                       app_revision=args['revision'],
                       input_=args['input'],
                       output=args['output'],
                       validate=args['validate'],
                       update=args['update'],
                       decompose=args['decompose'])


if __name__ == '__main__':
    sys.exit(main())
