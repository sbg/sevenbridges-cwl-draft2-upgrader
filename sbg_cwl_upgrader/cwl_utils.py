from copy import deepcopy
import jsbeautifier
from collections.abc import Mapping, Sequence
from termcolor import colored
import yaml
import os
import re
import hashlib
import json


class CWL(object):
    """
    Base class for CWL conversion, containing CWL methods used in conversion.
    """
    cwl = {}

    def to_dict(self):
        return self.cwl

    @staticmethod
    def shorten_type(type_obj):
        """
        Convert type to shorthand syntax, e.g. ["File", null] is converted
        to "File?"
        :param type_obj: str or list or dict representing CWL input/output.
        :return: list of types
        """

        # Don't shorten if nested inputBinding is added
        for t in as_list(type_obj):
            if isinstance(t, dict) and 'inputBinding' in t:
                return type_obj

        if isinstance(type_obj, str) or not isinstance(type_obj, Sequence):
            return type_obj
        new_type = []
        for entry in type_obj:
            if isinstance(entry, Mapping):
                if (entry['type'] == 'array' and
                        isinstance(entry['items'], str)):
                    entry = entry['items'] + '[]'
            new_type.extend([entry])
        type_obj = new_type
        if isinstance(type_obj, list):
            if len(type_obj) == 2:
                if 'null' in type_obj:
                    type_copy = deepcopy(type_obj)
                    type_copy.remove('null')
                    if isinstance(type_copy[0], str):
                        return type_copy[0] + '?'
            elif len(type_obj) == 1:
                type_obj = type_obj[0]
        return type_obj

    @staticmethod
    def _print_js_warnings(script: str):
        """
        Print JS warnings during conversion:
        - Missing return statement in expressions.
        :param script: Javascript expression
        """
        if script.find('return') == -1:
            print(
                colored('\nNo return statement in script:\n{}'.format(script),
                        'red')
            )

    def parse_js(self, script: str):
        """Convert draft2 JS objects to V1 JS objects"""
        lines = script.splitlines()

        # Wrap expression in ${}
        if script.strip().startswith("{") and script.strip().endswith("}"):
            new_script = '$' + '\n'.join(lines)
        elif len(lines) == 1 and 'return' not in lines[0]:
            # one-liners without return
            new_script = '${ return ' + lines[0] + '}'
        else:
            new_script = '${' + '\n'.join(lines) + '}'

        # Map draft2 objects and properties to v1 objects and properties
        new_script = new_script.replace('$job.inputs', 'inputs')
        new_script = new_script.replace(
            '$job.allocatedResources.mem', 'runtime.ram')
        new_script = new_script.replace(
            '$job.allocatedResources.cpu', 'runtime.cores')
        new_script = new_script.replace('$job.allocatedResources', 'runtime')
        new_script = new_script.replace('$self', 'self')
        # Sometimes people used ".name" in draft2
        new_script = new_script.replace('.name', '.basename')
        new_script = new_script.replace("['name']", "['basename']")
        new_script = jsbeautifier.beautify(new_script)
        new_script = new_script.replace('$ {', '${')
        # Solve different handling of null values
        new_script = re.sub(r'typeof (?P<var>.*) !== "undefined"',
                            r'\g<var>',
                            new_script)
        new_script = re.sub(r"typeof (?P<var>.*) !== 'undefined'",
                            r'\g<var>',
                            new_script)

        # Print out warnings about common issues
        self._print_js_warnings(new_script)

        return new_script

    def handle_sbg_metadata(self, out_metadata: dict):
        """
        Handle cases where metadata fields are implicitly set on outputs
        Do this by pre-pending a JS in outputEval.
        """
        metadata_scripted_functions = ''
        for meta_key, meta_val in out_metadata.items():
            # metadata value can be JS or string. Convert to string
            if isinstance(meta_val, dict):
                if not meta_val['script'].startswith('{'):
                    meta_val['script'] = '{ return ' + meta_val[
                        'script'] + ' }'
                metadata_scripted_functions += (
                    '\nvar add_metadata_key_{} = '
                    'function (self, inputs) {}'.format(
                        meta_key,
                        self.parse_js(meta_val['script']).lstrip('$')
                    )
                )
                out_metadata[meta_key] = (
                    'add_metadata_key_{}(self, inputs)'.format(meta_key)
                )

        add_js = '\n'.join([
            metadata_scripted_functions,
            '    for (var i=0; i < self.length; i++){',
            '      var out_metadata = {};'.format(str(out_metadata).replace(
                "'add_metadata_key_", "add_metadata_key_").replace(
                "(self, inputs)'", "(self[i], inputs)")
            ),
            '      self[i] = setMetadata(self[i], out_metadata)',
            '    };\n'])
        return add_js

    @staticmethod
    def get_record_position(record: dict):
        """Get CL position for a record type input"""
        for field in record['fields']:
            if 'inputBinding' in field:
                if 'position' in field['inputBinding']:
                    return field['inputBinding']['position']
                else:
                    return 1
        else:
            return None

    @staticmethod
    def handle_glob_brace(glob):
        if glob.startswith('{') and glob.endswith('}'):
            return [_s.strip() for _s in glob[1:-1].split(",")]
        return glob

    @staticmethod
    def wrap_expression(code: str):
        return jsbeautifier.beautify('${\n' + code + '\n}').replace('$ {',
                                                                    '${')

    @staticmethod
    def append_js(code: str, add: str):
        new_code = code.strip().rstrip('}')
        new_code = new_code + '\n' + add + '\n}'
        return jsbeautifier.beautify(new_code).replace('$ {', '${')

    @staticmethod
    def prepend_js(code: str, add: str):
        new_code = code.strip().lstrip('${')
        new_code = '${\n' + add + '\n' + new_code
        return jsbeautifier.beautify(new_code).replace('$ {', '${')

    @staticmethod
    def is_file_input(sbg_draft2_input: dict):
        """
        Check if draft2 input is File or File[]
        :param sbg_draft2_input: CWL input dict
        :return: boolean
        """
        if 'type' in sbg_draft2_input:
            for t in sbg_draft2_input['type']:
                if t == 'File':
                    return True
                elif (isinstance(t, dict) and
                      'items' in t and t['items'] == 'File'):
                    return True
            else:
                return False

    @staticmethod
    def is_array_input(sbg_draft2_input: dict):
        """
        Check if draft2 input is a list
        :param sbg_draft2_input: CWL input dict
        :return: boolean
        """
        if 'type' in sbg_draft2_input:
            for t in as_list(sbg_draft2_input['type']):
                if isinstance(t, dict) and 'items' in t:
                    return True
        else:
            return False

    @staticmethod
    def handle_id(m_id: str):
        """In CWL1 input/output ID shouldn't start with #"""
        m_id = deepcopy(m_id).lstrip('#')
        m_id = m_id.rsplit('.')[1] if m_id.count('.') > 0 else m_id
        return m_id


def as_list(l):
    if isinstance(l, list):
        return l
    return [l]


def calc_json_hash(json_dict):
    return hashlib.md5(
        json.dumps(json_dict, sort_keys=True).encode('utf-8')
    ).hexdigest()


def get_abs_path(path: str, base_dir: str):
    if os.path.isabs(path):
        abs_path = path
    elif path.startswith('../'):
        while path.startswith('../'):
            path = path[3:]
            base_dir = os.path.dirname(base_dir)
        abs_path = os.path.abspath(os.path.join(base_dir, path))
    elif path.startswith('./'):
        abs_path = os.path.abspath(os.path.join(base_dir, path[2:]))
    else:
        abs_path = os.path.abspath(os.path.join(base_dir, path))
    return abs_path


def resolve_cwl(cwl_app_path: str):
    """
    # Resolve local tool references to get a self-contained CWL dict
    :param cwl_app_path: string Local CWL path
    :return: dict Resolved CWL dict
    """
    base_dir = os.path.dirname(os.path.abspath(cwl_app_path))
    with open(cwl_app_path, 'r') as f:
        cwl_dict = yaml.safe_load(f)
    if cwl_dict['class'] in ['CommandLineTool', 'ExpressionTool']:
        return cwl_dict
    elif cwl_dict['class'] == 'Workflow':
        if isinstance(cwl_dict['steps'], dict):
            for step_id, step in cwl_dict['steps'].items():
                if isinstance(step['run'], str):
                    cwl_dict['steps'][step_id]['run'] = resolve_cwl(
                        get_abs_path(step['run'], base_dir))
        elif isinstance(cwl_dict['steps'], list):
            for i, step in enumerate(cwl_dict['steps']):
                if isinstance(step['run'], str):
                    cwl_dict['steps'][i]['run'] = resolve_cwl(
                        get_abs_path(step['run'], base_dir))
    return cwl_dict


def cwl_ensure_dict(cwl_list, id_key: str):
    """
    Esure map syntax where list with unique ID is allowed
    :param cwl_list: list or dict
    :param id_key: unique list ID from CWL spec
    :return: dict
    """

    return cwl_list if isinstance(cwl_list, dict) else cwl_list_to_dict(
        cwl_list, id_key)


def cwl_ensure_array(cwl_dict, id_key: str):
    """
    Esure array syntax where list with unique ID is allowed
    :param cwl_dict: list or dict
    :param id_key: unique list ID from CWL spec
    :return: dict
    """

    return cwl_dict if isinstance(cwl_dict, list) else cwl_dict_to_list(
        cwl_dict, id_key
    )


def cwl_dict_to_list(cwl_dict: list, id_key: str):
    """Convert dict with id_key as unique element ID to list"""
    out = []
    cwl_dict = deepcopy(cwl_dict)
    for id_, item in cwl_dict.items():
        it = item
        it[id_key] = id_
        out.append(it)

    return out


def cwl_list_to_dict(cwl_list: list, id_key: str):
    """Convert list with id_key as unique element ID to dict"""
    cwl_list = deepcopy(cwl_list)
    return {f[id_key]: remove_dict_key(f, id_key) for f in cwl_list}


def remove_dict_key(dct, key):
    d = deepcopy(dct)
    del d[key]
    return d


def yaml_ext():
    return {'.yml', '.yaml', '.cwl'}


def json_ext():
    return {'.json'}


def is_local(x):
    if x:
        return x.endswith(tuple(yaml_ext().union(json_ext())))
    return False


def add_revision_note(raw_cwl, rev_note):
    out = deepcopy(raw_cwl)
    out['sbg:revisionNotes'] = rev_note
    return out
