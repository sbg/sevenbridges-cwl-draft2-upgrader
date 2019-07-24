import argparse
import logging
from termcolor import colored
import sevenbridges as sbg
from sevenbridges.http.error_handlers import (
    general_error_sleeper, maintenance_sleeper, rate_limit_sleeper
)


logger = logging.getLogger(__name__)


def get_endpoint(platform: str):
    """
    Return Api url by platform name.
    :param platform: igor, cgc, gcp, cavatica
    :return: api url
    """
    if platform in ['igor', 'sbpla', 'default']:
        return "https://api.sbgenomics.com/v2"
    elif platform == 'cgc':
        return "https://cgc-api.sbgenomics.com/v2"
    elif platform == 'eu':
        return "https://eu-api.sbgenomics.com/v2"
    elif platform == 'cn':
        return "https://cn-api.sbgenomics.com/v2"
    elif platform == 'f4c':
        return "https://f4c-api.sbgenomics.com/v2"
    elif platform == 'cavatica':
        return "https://cavatica-api.sbgenomics.com/v2"
    else:
        raise ValueError('Unsupported platform')


def init_api(profile='default', platform=None, dev_token=None, endpoint=None):
    """
    Initialize SBG API using credentials located inside
    $HOME/.sevenbridges/credentials or by provided dev_token and platform.
    :param profile: profile listed inside $HOME/.sevenbridges/credentials.
                    Example: cgc, default, cavatica
    :param platform: Predefined platform.
                     Available: igor, cgc, f4c, eu, cn, cavatica
    :param dev_token: developer token from platform
    :param endpoint: api endpoint
    :return: sbg.Api
    """

    if platform and not endpoint:
        endpoint = get_endpoint(platform)

    if dev_token and not endpoint:
        endpoint = get_endpoint('igor')

    if dev_token and endpoint:
        api = sbg.Api(
            url=endpoint, token=dev_token,
            error_handlers=[
                rate_limit_sleeper, maintenance_sleeper, general_error_sleeper
            ]
        )
    else:
        c = sbg.Config(profile=profile)
        api = sbg.Api(
            config=c,
            error_handlers=[
                rate_limit_sleeper, maintenance_sleeper, general_error_sleeper
            ]
        )
    return api


def add_sbg_auth_to_args(parser: argparse.ArgumentParser):
    """
    Add SBG authentication parameters to argument parser
    :param parser: argument parser
    :return:
    """

    parser.add_argument('--profile', default='default',
                        help='profile in sevenbridges config file')
    parser.add_argument('--token', help='developer token for the API')
    parser.add_argument('--platform', default='igor',
                        help='platform name: igor, cgc, cavatica, eu, cn, f4c')
    parser.add_argument('--endpoint', help='API endpoint')


def add_logging_to_args(parser: argparse.ArgumentParser):
    """
    Add log_lvl and log file path to argument parser
    :param parser: argument parser
    :return:
    """
    parser.add_argument('--log',
                        default='log',
                        help='log file path')
    parser.add_argument('--log_lvl',
                        default='WARN',
                        help='Set minimal level of logging '
                             '(ERROR > WARN > INFO).Available '
                             'options:\n{ERROR, WARN, INFO} [default: WARN]')


def configure_logging(args: dict):
    """
    Configure logging
    :param args: argparse arguments
    :return:
    """
    if args['log_lvl'] == 'ERROR':
        log_lvl = logging.ERROR
    elif args['log_lvl'] == 'WARN':
        log_lvl = logging.WARN
    else:
        log_lvl = logging.INFO

    logging.basicConfig(
        level=log_lvl,
        filename=args['log'],
        format='%(levelname)-11s - %(message)s [%(name)s:%(lineno)d]'
    )


def print_and_log_info(msg, color='green'):
    print(colored(msg, color))
    logger.info(msg)
