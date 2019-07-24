import yaml
import os.path
import sys
import argparse
from sbg_cwl_upgrader.sbg_utils import (add_sbg_auth_to_args,
                                        configure_logging,
                                        add_logging_to_args, init_api)
from sbg_cwl_upgrader.validator.cwl_validation import CWLValidator
from sbg_cwl_upgrader.cwl_utils import is_local


def create_arg_parser():
    parser = argparse.ArgumentParser(
        description='Check for JS ES5.1 strict syntax conformance. '
                    'Check variables not defined or ES6 features are used.')

    parser.add_argument('-i', '--input', required=True,
                        help='local CWL file path or platform app ID.')
    add_logging_to_args(parser)
    add_sbg_auth_to_args(parser)

    return parser


def main(args=sys.argv[1:]):
    """
    Entrypoint and CLI for sbg_validate_js_cwl_v1 tool
    """

    args = vars(create_arg_parser().parse_args(args))

    input_cwl = args.get("input")

    configure_logging(args)

    validator = CWLValidator()

    if is_local(input_cwl):
        if not os.path.isfile(input_cwl):
            raise FileNotFoundError("Can\'t locate file: \"" +
                                    input_cwl + "\". Check --input argument.")
        else:
            with open(input_cwl) as tool_json_file:
                cwl_code = yaml.safe_load(tool_json_file)
    else:
        api = init_api(profile=args['profile'], platform=args['platform'],
                       dev_token=args['token'], endpoint=args['endpoint'])
        cwl_code = api.apps.get(input_cwl).raw

    validator.validate(cwl_code)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
