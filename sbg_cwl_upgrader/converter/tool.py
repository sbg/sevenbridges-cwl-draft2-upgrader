import re
from copy import deepcopy
from sbg_cwl_upgrader.cwl_utils import CWL
import os
import sbg_cwl_upgrader
from termcolor import colored

EXPRESSION_LIB = os.path.join(
    os.path.abspath(os.path.dirname(sbg_cwl_upgrader.__file__)),
    'resources/expression_lib.js')


class InputRecordField(CWL):
    def __init__(self, sbg_draft2=None):
        if sbg_draft2:
            self.cwl = Input(sbg_draft2).to_dict()


class Expression(CWL):
    def __init__(self, sbg_draft2=None):
        if sbg_draft2:
            self.cwl = self.parse_js(sbg_draft2['script'])


class CommandLineBinding(CWL):
    def __init__(self, sbg_draft2=None):
        if sbg_draft2:
            self.cwl = {x: y for x, y in deepcopy(sbg_draft2).items()
                        if y is not None}
            self.cwl['shellQuote'] = False
            if ('valueFrom' in sbg_draft2
                    and isinstance(sbg_draft2['valueFrom'], dict)
                    and 'script' in sbg_draft2['valueFrom']):
                self.cwl['valueFrom'] = Expression((
                    sbg_draft2['valueFrom'])).to_dict()
            if 'id' in self.cwl:
                del self.cwl['id']

            if 'secondaryFiles' in self.cwl:
                del self.cwl['secondaryFiles']


class Input(CWL):
    def __init__(self, sbg_draft2=None, in_id=''):
        if sbg_draft2:
            self.cwl = deepcopy(sbg_draft2)
            if 'description' in self.cwl:
                self.cwl['doc'] = self.cwl['description']
                del self.cwl['description']

            if 'inputBinding' in self.cwl:
                if 'secondaryFiles' in self.cwl['inputBinding']:
                    self.cwl['secondaryFiles'] = []
                    for item in self.cwl['inputBinding']['secondaryFiles']:
                        if isinstance(item, dict):
                            self.cwl['secondaryFiles'].append(
                                Expression(sbg_draft2=item).to_dict())
                        elif isinstance(item, str):
                            self.cwl['secondaryFiles'].append(item)
                        else:
                            raise Exception(
                                "Secondary files can be "
                                "either instance of str or dict.")

            if 'inputBinding' in self.cwl:
                self.cwl['inputBinding'] = CommandLineBinding(
                        sbg_draft2=self.cwl['inputBinding']).to_dict()

                # Place a "default: 0" field
                # for non-file inputs with valueFrom,
                # then convert to null
                if ('valueFrom' in self.cwl['inputBinding']
                        and not self.is_file_input(sbg_draft2) and in_id):
                    self.cwl['default'] = 0
                    self.cwl['inputBinding']['valueFrom'] = self.prepend_js(
                        self.cwl['inputBinding']['valueFrom'],
                        'if (self == 0){self = null;\ninputs.' +
                        in_id + ' = null};\n')

                if self.is_array_input(sbg_draft2):
                    # itemSeparator must go with prefix
                    if ('itemSeparator' in self.cwl['inputBinding']
                            and 'prefix' not in self.cwl['inputBinding']):
                        del self.cwl['inputBinding']['itemSeparator']
                    # In sbg:draft2 "itemSeparator: null" meant repeat prefix.
                    # Move "prefix" and "separate" to new inputBinding for item
                    # Try to add valueFrom as well
                    if (self.cwl['inputBinding'].get(
                            'itemSeparator', None) is None
                            and 'prefix' in self.cwl['inputBinding']):
                        self.cwl = self.repeat_prefix_handler()

                if 'sbg:cmdInclude' in self.cwl['inputBinding']:
                    del self.cwl['inputBinding']['sbg:cmdInclude']

            if 'required' in self.cwl:
                del self.cwl['required']

            if 'type' in self.cwl:
                for t in self.cwl['type']:
                    if t != 'null' and 'fields' in t:
                        t['fields'] = [InputRecordField(x).to_dict()
                                       for x in t['fields']]
                        if (self.get_record_position(t)
                                and 'inputBinding' not in t):
                            self.cwl['inputBinding'] = {
                                'position': self.get_record_position(t)
                            }
                    if 'name' in t:
                        t['name'] = in_id
                self.cwl['type'] = self.shorten_type(self.cwl['type'])

    def repeat_prefix_handler(self):
        """
        Handle case with null in itemSeparator in draft2 inputs
        """
        self.cwl['inputBinding'].pop('itemSeparator', None)
        prefix = self.cwl['inputBinding']['prefix']
        new_binding = {
            'prefix': prefix
        }
        del self.cwl['inputBinding']['prefix']
        separate = ' '
        if 'separate' in self.cwl['inputBinding']:
            new_binding['separate'] = self.cwl['inputBinding']['separate']
            if self.cwl['inputBinding']['separate'] is False:
                separate = ''
            del self.cwl['inputBinding']['separate']

        is_file = False
        if isinstance(self.cwl['type'], list):
            for i, t in enumerate(self.cwl['type']):
                if isinstance(t, dict):
                    if t.get('items', "") == "File":
                        is_file = True
                    self.cwl['type'][i]['inputBinding'] = new_binding
        elif isinstance(self.cwl['type'], dict):
            if self.cwl['type'].get('items', "") == "File":
                is_file = True
            self.cwl['type']['inputBinding'] = new_binding

        # Add valueFrom to ensure array if possible
        if "valueFrom" not in self.cwl["inputBinding"]:
            item = ("[].concat(self)[i].path" if is_file
                    else "[].concat(self)[i]")
            self.cwl["inputBinding"]["valueFrom"] = '\n'.join([
                "${",
                "    var out = \"\"",
                "    for (var i = 0; i < [].concat(self).length; i++ ){",
                "        out += \" {}{}\" + {}".format(prefix, separate, item),
                "    }    ",
                "    return out",
                "}"
            ])

        return self.cwl


class OutputBinding(CWL):
    def __init__(self, sbg_draft2=None):

        if sbg_draft2:
            self.cwl = deepcopy(sbg_draft2)
            if ('glob' in sbg_draft2
                    and isinstance(sbg_draft2['glob'], dict)
                    and 'script' in sbg_draft2['glob']):
                self.cwl['glob'] = self.parse_js(sbg_draft2['glob']['script'])

            # Handle sub-folder glob in draft2
            if (self.cwl.get('glob', '').startswith('./')
                    and len(self.cwl.get('glob', '')) > 2):
                self.cwl['glob'] = self.cwl['glob'][2:]

            # Handle brace expand in glob
            if isinstance(self.cwl.get('glob', None), str):
                self.cwl['glob'] = self.handle_glob_brace(self.cwl.get('glob'))

            if ('outputEval' in sbg_draft2
                    and isinstance(sbg_draft2['outputEval'], dict)
                    and 'script' in sbg_draft2['outputEval']):
                self.cwl['outputEval'] = self.parse_js(
                    sbg_draft2['outputEval']['script'])

            # First prepend setting specific keys
            if 'sbg:metadata' in self.cwl:
                add_metadata_js = self.handle_sbg_metadata(
                    self.cwl['sbg:metadata'])
                if 'outputEval' in self.cwl:
                    self.cwl['outputEval'] = self.prepend_js(
                        self.cwl['outputEval'], add_metadata_js)
                else:
                    self.cwl['outputEval'] = self.wrap_expression(
                        add_metadata_js + '\nreturn self\n')
                del self.cwl['sbg:metadata']
            # Then prepend inheriting
            if 'sbg:inheritMetadataFrom' in self.cwl:
                inp_id = self.cwl['sbg:inheritMetadataFrom'].lstrip('#')
                val = 'inheritMetadata(self, inputs.' + inp_id + ')\n'
                if 'outputEval' in self.cwl:
                    self.cwl['outputEval'] = self.prepend_js(
                        self.cwl['outputEval'], 'self = ' + val + ';')
                else:
                    self.cwl['outputEval'] = self.wrap_expression(
                        'return ' + val)
                del self.cwl['sbg:inheritMetadataFrom']
            if 'id' in self.cwl:
                del self.cwl['id']
            if 'secondaryFiles' in self.cwl:
                del self.cwl['secondaryFiles']


class Output(CWL):
    def __init__(self, sbg_draft2=None):
        if sbg_draft2:
            self.cwl = deepcopy(sbg_draft2)
            if 'description' in self.cwl:
                self.cwl['doc'] = self.cwl['description']
                del self.cwl['description']

            if 'outputBinding' in self.cwl:
                if 'secondaryFiles' in self.cwl['outputBinding']:
                    self.cwl['secondaryFiles'] = \
                        self.cwl['outputBinding']['secondaryFiles']
                self.cwl['outputBinding'] = OutputBinding(
                    sbg_draft2=self.cwl['outputBinding']).to_dict()

            if 'required' in self.cwl:
                del self.cwl['required']

            if 'type' in self.cwl:
                self.cwl['type'] = self.shorten_type(sbg_draft2['type'])


class CWLToolConverter(CWL):
    @staticmethod
    def _is_staged_file(sbg_draft2_input):
        if ('sbg:stageInput' in sbg_draft2_input
                and sbg_draft2_input['sbg:stageInput']
                and 'type' in sbg_draft2_input
                and isinstance(sbg_draft2_input['type'], list)):
            input_copy = deepcopy(sbg_draft2_input)
            if 'null' in input_copy['type']:
                input_copy['type'].remove('null')
            draft2_type = input_copy['type'][0]
            if isinstance(draft2_type, str) and draft2_type == 'File':
                return True
        return False

    @staticmethod
    def _is_staged_array_of_files(sbg_draft2_input):
        if ('sbg:stageInput' in sbg_draft2_input
                and sbg_draft2_input['sbg:stageInput']
                and 'type' in sbg_draft2_input
                and isinstance(sbg_draft2_input['type'], list)):
            input_copy = deepcopy(sbg_draft2_input)
            if 'null' in input_copy['type']:
                input_copy['type'].remove('null')
            draft2_type = input_copy['type'][0]
            if (isinstance(draft2_type, dict)
                    and 'type' in draft2_type
                    and draft2_type['type'] == 'array'
                    and draft2_type['items'] == 'File'):
                return True
        return False

    @staticmethod
    def _stage_inputs(draft2_inputs):
        out = []
        for i in draft2_inputs:
            if 'sbg:stageInput' in i and i['sbg:stageInput']:
                out.append(
                    {
                        "entry": "$(inputs." + str(i['id']).lstrip('#') + ")",
                        "writable": i['sbg:stageInput'] == 'copy'
                    }
                )
        return out

    @staticmethod
    def _handle_inputs(inputs: list,
                       base_command: list,
                       offset=None,
                       min_inp_pos=0):
        new_inputs = {}
        for inp_i in inputs:
            in_id = inp_i['id'].lstrip('#')
            new_inputs[in_id] = deepcopy(inp_i)
            del new_inputs[in_id]['id']
            if 'sbg:stageInput' in new_inputs[in_id]:
                del new_inputs[in_id]['sbg:stageInput']
            new_inputs[in_id] = Input(sbg_draft2=new_inputs[in_id],
                                      in_id=in_id).to_dict()
            if isinstance(offset, int) and 'inputBinding' in new_inputs[in_id]:
                if 'position' in new_inputs[in_id]['inputBinding']:
                    new_inputs[in_id]['inputBinding']['position'] = int(
                        new_inputs[in_id]['inputBinding']['position']) + len(
                        base_command) - offset - min_inp_pos
                else:
                    new_inputs[in_id]['inputBinding']['position'] = len(
                        base_command) - offset - min_inp_pos
        return new_inputs

    @staticmethod
    def _handle_outputs(outputs):
        new_outputs = {}
        for output in outputs:
            o_id = output['id'].lstrip('#')
            new_outputs[o_id] = deepcopy(output)
            del new_outputs[o_id]['id']
            new_outputs[o_id] = Output(sbg_draft2=new_outputs[o_id]).to_dict()
        return new_outputs

    @staticmethod
    def _handle_hints(hints):
        new_hints = []
        for hint in hints:
            if (isinstance(hint, dict) and
                    'class' in hint.keys() and
                    hint['class'] not in ['sbg:CPURequirement',
                                          'sbg:MemRequirement',
                                          'DockerRequirement']):
                new_hints.append(hint)
        return new_hints

    def _handle_requirements(self, hints, requirements, inputs):

        new_requirements = []
        resource_requirement = None
        initial_work_dir_requirement = {
            'class': 'InitialWorkDirRequirement',
            'listing': []
        }

        for hint in hints:
            if isinstance(hint, dict) and 'class' in hint.keys():
                # DockerRequirement
                if hint['class'] == 'DockerRequirement':
                    if 'dockerImageId' in hint:
                        del hint['dockerImageId']
                    new_requirements.append(deepcopy(hint))
                # ResourceRequirement
                elif ((hint['class'] == 'sbg:CPURequirement')
                        or (hint['class'] == 'sbg:MemRequirement')):
                    if resource_requirement is None:
                        resource_requirement = {'class': 'ResourceRequirement'}
                        new_requirements.append(resource_requirement)
                    cpu_mem_map = {
                        'sbg:CPURequirement': 'coresMin',
                        'sbg:MemRequirement': 'ramMin'
                    }

                    k_mapped = cpu_mem_map[hint['class']]

                    if isinstance(hint['value'], int):
                        resource_requirement[k_mapped] = int(hint['value'])
                    elif (isinstance(hint['value'], dict)
                            and 'class' in hint['value']
                            and 'script' in hint['value']
                            and hint['value']['class'] == 'Expression'):
                        resource_requirement[k_mapped] = self.parse_js(
                            hint['value']['script'])

                    else:
                        raise Exception('Unsupported resource requirement!',
                                        hint)
            else:
                raise Exception('Attribute class has to be member of hint')

        for requirement in requirements:
            if isinstance(requirement, dict) and 'class' in requirement.keys():
                # Create files
                if requirement['class'] == 'CreateFileRequirement':
                    for file in requirement['fileDef']:
                        if (isinstance(file['filename'], dict)
                                and 'script' in file['filename']):
                            entryname = self.parse_js(
                                file['filename']['script'])
                        else:
                            entryname = file['filename']

                        # Check if file is being created in subfolder and warn
                        if isinstance(entryname, str) and '/' in entryname:
                            msg = "Can't create file in subfolder in CWL1. " \
                                  "Please modify name of the file {}".format(
                                    entryname)
                            print(colored(msg, 'red'))
                        if (isinstance(file['fileContent'], dict)
                                and 'script' in file['fileContent']):
                            entry = self.parse_js(
                                file['fileContent']['script'])
                        else:
                            entry = self._handle_bash(file['fileContent'])

                        initial_work_dir_requirement['listing'].append({
                            'entryname': entryname,
                            'entry': entry
                        })
                # EnvVarRequirement
                elif requirement['class'] == 'EnvVarRequirement':
                    new_requirements.append(deepcopy(requirement))
        initial_work_dir_requirement[
            'listing'] += CWLToolConverter._stage_inputs(inputs)

        with open(EXPRESSION_LIB, 'r') as fp:
            new_requirements.insert(0, {"class": "InlineJavascriptRequirement",
                                        "expressionLib": [fp.read()]})

        new_requirements.insert(0, {"class": "ShellCommandRequirement"})
        new_requirements.append(initial_work_dir_requirement)

        return new_requirements

    @staticmethod
    def _handle_base_command(base_command):
        out = []
        offset = 0
        for x in base_command:
            if isinstance(x, dict):
                break
                # out.append(Expression(sbg_draft2=x).to_dict())
            elif isinstance(x, str):
                if re.match(r'[^A-Za-z0-9]+', x):
                    break
                else:
                    out += x.split()
            else:
                raise Exception("Base command type can be either"
                                " array of Strings or Expressions.")
            offset += 1
        # return out
        return offset, out

    @staticmethod
    def _handle_arguments(arguments, base_command, offset=None, min_inp_pos=0):
        out = []
        if isinstance(offset, int):
            for i in range(offset, len(base_command)):
                if isinstance(base_command[i], dict):
                    obj = dict(shellQuote=False,
                               position=i - offset,
                               valueFrom=Expression(
                                   sbg_draft2=base_command[i]).to_dict())

                    out.append(obj)
                elif isinstance(base_command[i], str):
                    obj = dict(shellQuote=False,
                               position=i - offset,
                               valueFrom=base_command[i])

                    out.append(obj)
                else:
                    raise Exception("Base command type can be either "
                                    "array of Strings or Expressions.")

        for arg in arguments:
            if isinstance(arg, dict):
                obj = CommandLineBinding(sbg_draft2=arg).to_dict()
                prev_position = 0
                if 'position' in obj and isinstance(obj['position'], int):
                    prev_position = obj['position']
                obj['position'] = \
                    prev_position + len(base_command) - offset - min_inp_pos
                out.append(obj)
            elif isinstance(arg, str):
                out.append(arg)
            else:
                raise Exception("Argument type can be either"
                                " String or Expression.")
        return out

    @staticmethod
    def _handle_stream(stream):
        if isinstance(stream, str):
            return stream
        elif isinstance(stream, dict):
            return Expression(sbg_draft2=stream).to_dict()
        else:
            raise Exception("Streams should be instance "
                            "of String or Expression")

    @staticmethod
    def _cleanup_invalid_inherit_metadata(inputs, outputs):
        input_ids = [inp['id'] for inp in inputs if 'id' in inp]
        for out in outputs:
            output_binding = out.get('outputBinding', None)
            if output_binding and 'sbg:inheritMetadataFrom' in output_binding:
                inherit_metadata_id = output_binding['sbg:inheritMetadataFrom']
                if inherit_metadata_id not in input_ids:
                    del out['outputBinding']['sbg:inheritMetadataFrom']
            else:
                continue
        return outputs

    @staticmethod
    def _get_lowest_negative_input_position(inputs):
        min_inp = 0
        for inp in inputs:
            if inp.get('inputBinding', {}).get('position', 0) < min_inp:
                min_inp = inp.get('inputBinding', {}).get('position', 0)
        return min_inp

    @staticmethod
    def _handle_bash(literal):
        return literal.replace('$(', '$("$")(').replace('${', '$("$"){')

    def convert_dict(self, data: dict):
        """Main method for converting draft2 tool to CWL1.0"""

        # Just reuse if tool is already CWLv1.0
        if data.get('cwlVersion') != 'sbg:draft-2':
            return data

        new_data = {k: deepcopy(v)
                    for k, v in data.items()
                    if k not in ['baseCommand', 'description', 'cwlVersion',
                                 'inputs', 'outputs', 'requirements',
                                 'arguments', 'stdin', 'stdout',
                                 'sbg:appVersion', 'hints', 'sbg:job',
                                 'sbg:modifiedBy', 'sbg:modifiedOn',
                                 'sbg:projectName', 'x', 'y', 'appUrl',
                                 'sbg:revision', 'sbg:revisionsInfo',
                                 'sbg:createdOn']}

        new_data['cwlVersion'] = 'v1.0'
        new_data['sbg:appVersion'] = ['v1.0']
        if 'stdin' in data:
            new_data['stdin'] = self._handle_stream(data['stdin'])
        if 'stdout' in data:
            new_data['stdout'] = self._handle_stream(data['stdout'])
        if 'description' in data:
            new_data['doc'] = data['description']

        # Add requirements if not empty
        new_requirements = self._handle_requirements(
                data.get('hints', []),
                data.get('requirements', []),
                data.get('inputs', [])
            )
        if new_requirements:
            new_data['requirements'] = new_requirements
        # Add hints if not empty
        new_hints = self._handle_hints(
            data.get('hints', [])
        )
        if new_hints:
            new_data['hints'] = new_hints

        min_inp_pos = self._get_lowest_negative_input_position(data['inputs'])

        offset, base_command = self._handle_base_command(
            data.get('baseCommand', []))

        new_data['baseCommand'] = base_command

        new_data['arguments'] = self._handle_arguments(
            data['arguments'] if 'arguments' in data else [],
            data['baseCommand'] if 'baseCommand' in data else [],
            offset=offset,
            min_inp_pos=min_inp_pos)

        if 'inputs' in data:
            new_data['inputs'] = self._handle_inputs(
                data['inputs'] if 'inputs' in data else [],
                data['baseCommand'] if 'baseCommand' in data else [],
                offset=offset,
                min_inp_pos=min_inp_pos)

        data['outputs'] = self._cleanup_invalid_inherit_metadata(
            data['inputs'], data['outputs'])
        if 'outputs' in data:
            new_data['outputs'] = self._handle_outputs(
                data['outputs'] if 'outputs' in data else [])

        return new_data
