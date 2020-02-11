from copy import deepcopy
from multiprocessing import cpu_count

import tqdm
from billiard.pool import Pool
from sbg_cwl_upgrader.cwl_utils import CWL
from sbg_cwl_upgrader.cwl_utils import as_list
from sbg_cwl_upgrader.converter.tool import CWLToolConverter
from sbg_cwl_upgrader.converter.connection_checker import ConnectionChecker


class CWLWorkflowConverter(CWL):

    @staticmethod
    def handle_source(source: list):
        source = deepcopy(source)
        out = []
        for s in as_list(source):
            s = s.lstrip('#').replace('.', '/')
            out.append(s)
        return out

    def handle_input(self, draft2_input):
        v1_input = deepcopy(draft2_input)

        if 'id' in v1_input:
            v1_input['id'] = self.handle_id(v1_input['id'])
        # if 'sbg:fileTypes' in input:
            # input['format'] = input['sbg:fileTypes']
            # del input['sbg:fileTypes']
        if 'required' in v1_input:
            del v1_input['required']
        if 'description' in v1_input:
            v1_input['doc'] = deepcopy(v1_input['description'])
            del v1_input['description']
        if 'type' in v1_input:
            v1_input['type'] = self.shorten_type(v1_input['type'])
        if 'source' in v1_input:
            v1_input['source'] = self.handle_source(v1_input['source'])
        # Legacy editor added useless valueFrom on wf inputs at some point
        if 'inputBinding' in v1_input:
            if 'valueFrom' in v1_input['inputBinding']:
                del v1_input['inputBinding']['valueFrom']
                if not v1_input['inputBinding']:
                    del v1_input['inputBinding']
        return v1_input

    def handle_inputs(self, inputs):
        result = []
        inputs = deepcopy(inputs)
        for inp in inputs:
            result.append(self.handle_input(inp))
        return result

    def handle_output(self, output):
        output = deepcopy(output)
        if 'id' in output:
            output['id'] = self.handle_id(output['id'])
        # if 'sbg:fileTypes' in output:
            # output['format'] = output['sbg:fileTypes']
            # del output['sbg:fileTypes']
        if 'required' in output:
            del output['required']
        if 'description' in output:
            output['doc'] = deepcopy(output['description'])
            del output['description']
        if 'type' in output:
            output['type'] = self.shorten_type(output['type'])
        if 'source' in output:
            output['source'] = self.handle_source(output['source'])
        return output

    def handle_outputs(self, outputs):
        result = []
        outputs = deepcopy(outputs)
        for o in outputs:
            result.append(self.handle_output(o))
        return result

    def handle_step(self, step):
        step = deepcopy(step)

        if 'id' in step:
            step['id'] = self.handle_id(step['id'])
        if 'inputs' in step:
            step['in'] = self.handle_inputs(step['inputs'])
            del step['inputs']
        if 'outputs' in step:
            step['out'] = self.handle_outputs(step['outputs'])
            del step['outputs']
        if 'run' in step:
            step['run'] = self.parse_step(step['run'], step.get('id', 'No ID'))
        if 'scatter' in step:
            step['scatter'] = self.handle_id(step['scatter'])
        return step

    def handle_steps(self, steps):
        def map_out(x):
            if step_index in x:
                del x[step_index]
            return x

        step_index = 'step_index'
        steps = deepcopy(steps)
        for i, s in enumerate(steps):
            s[step_index] = i

        out = [x for x in
               map(map_out,
                   sorted([done for done in
                           tqdm.tqdm(get_pool().imap_unordered(
                               self.handle_step, steps),
                               total=len(steps),
                               leave=True,
                               desc='Workflow steps')],
                          key=lambda x: x[step_index]))]
        return out

    @staticmethod
    def parse_step(data: dict, step_id: str):
        if 'class' in data and isinstance(data['class'], str):
            if data['class'] == 'CommandLineTool':
                return CWLToolConverter().convert_dict(data)
            elif data['class'] == 'Workflow':
                return CWLWorkflowConverter().convert_dict(data)
            else:
                raise ValueError(
                    'Invalid cwl class in step {}.'.format(step_id)
                )
        else:
            raise ValueError('Invalid cwl class in step {}.'.format(step_id))

    @staticmethod
    def default_requirements():
        return [{'class': 'ScatterFeatureRequirement'},
                {'class': 'MultipleInputFeatureRequirement'},
                {'class': 'SubworkflowFeatureRequirement'},
                {'class': 'InlineJavascriptRequirement'},
                {'class': 'StepInputExpressionRequirement'}]

    def convert_dict(self, data: dict) -> dict:
        v1_0_data = {k: deepcopy(v) for k, v in data.items()
                     if k not in ['x', 'y', 'appUrl']}
        if v1_0_data.get('cwlVersion') != 'sbg:draft-2':

            return v1_0_data
        v1_0_data['cwlVersion'] = 'v1.0'
        v1_0_data['sbg:appVersion'] = [v1_0_data['cwlVersion']]
        v1_0_data['inputs'] = self.handle_inputs(v1_0_data['inputs'])
        v1_0_data['outputs'] = self.handle_outputs(v1_0_data['outputs'])
        v1_0_data['requirements'] = self.default_requirements()
        if 'description' in v1_0_data:
            v1_0_data['doc'] = deepcopy(v1_0_data['description'])
            del v1_0_data['description']
        for o in v1_0_data['outputs']:
            o['id'] = self.handle_id(o['id'])
            o['outputSource'] = self.handle_source(o['source'])
            del o['source']
        if 'steps' in v1_0_data and isinstance(v1_0_data['steps'], list):
            v1_0_data['steps'] = self.handle_steps(v1_0_data['steps'])
        connection_checker = ConnectionChecker()
        v1_0_data = connection_checker.fix_terminal_output_types(v1_0_data)
        v1_0_data = connection_checker.fix_connection_matching(v1_0_data)
        return v1_0_data


def get_pool(pool=None):
    if not pool:
        pool = Pool(cpu_count())
    return pool
