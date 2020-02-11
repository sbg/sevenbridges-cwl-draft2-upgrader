from sbg_cwl_upgrader.cwl_utils import (cwl_ensure_dict,
                                        cwl_ensure_array,
                                        as_list)
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)

JS_ITEM_TO_LIST = "$(self ? [].concat(self) : self)"
JS_LIST_TO_ITEM = "$(self ? [].concat(self)[0] : self)"


class ConnectionChecker(object):

    @staticmethod
    def scattered_type(t):
        return {"type": "array", "items": t}

    def extract_source_type(self, source, cwl):
        """
        Extract type of a connection source
        :param source: string
        :param cwl: dict
        :return: string or dict
        """
        if '/' in source:
            source_step_id = source.split('/')[0]
            source_step_out_id = source.split('/')[1]
            source_step = cwl_ensure_dict(cwl['steps'], 'id')[source_step_id]
            source_type = cwl_ensure_dict(
                source_step['run']['outputs'], 'id'
            )[source_step_out_id]['type']
            if "scatter" in source_step:
                source_type = self.scattered_type(source_type)
        else:
            source_type = cwl_ensure_dict(cwl['inputs'], 'id')[source]['type']
        return source_type

    def extract_incoming_type(self, sources, cwl, flatten):
        """
        Extract type of connection sources
        :param sources: list of source strings
        :param cwl: dict
        :param flatten: boolean
        :return:
        """
        if len(sources) == 0:
            return None
        elif len(sources) == 1:
            return self.extract_source_type(sources[0], cwl)
        else:
            # Avoid getting all source types
            # Take first and assume other sources are same type
            # TODO extract different types
            types = self.extract_source_type(sources[0], cwl)
            if flatten:
                if isinstance(types, dict) and types["type"] == "array":
                    return types
                else:
                    return self.scattered_type(types)
            else:
                return self.scattered_type(types)

    @staticmethod
    def remove_null(s_type):
        """
        Strip null from types in optional type
        :param s_type: any cwl type or list of types
        :return: any cwl type
        """
        if isinstance(s_type, list):
            for t in s_type:
                if t != "null":
                    return t
        elif isinstance(s_type, str):
            return s_type.rstrip('?')
        return s_type

    def unpack_list(self, s_type):
        """
        Unpack shorthand syntax ([]) for array type
        :param s_type: any cwl type
        :return: any cwl type or list of types
        """
        if isinstance(s_type, str) and s_type.endswith("[]"):
            return self.scattered_type(s_type.rstrip("[]"))
        return s_type

    def transform_type(self, source_type, sink_type):
        """
        Return valueFrom expression to cover connection type mismatch
        :param source_type: any cwl type
        :param sink_type: any cwl type
        :return: valueFrom expression or None
        """
        # Fix this to cover more types
        source_type = self.unpack_list(self.remove_null(source_type))
        sink_type = self.unpack_list(self.remove_null(sink_type))
        if isinstance(source_type, dict) and not isinstance(sink_type, dict):
            return JS_LIST_TO_ITEM
        elif isinstance(sink_type, dict) and not isinstance(source_type, dict):
            return JS_ITEM_TO_LIST
        elif isinstance(source_type, dict) and isinstance(sink_type, dict):
            if source_type['type'] == 'array' and sink_type['type'] == 'array':
                return self.transform_type(source_type['items'],
                                           sink_type['items'])
            elif (source_type['type'] == 'array' and
                  sink_type['type'] != 'array'):
                return JS_LIST_TO_ITEM
            elif (source_type['type'] != 'array' and
                  sink_type['type'] == 'array'):
                return JS_ITEM_TO_LIST
        return None

    @staticmethod
    def is_optional(s_type):
        """
        Check if cwl type is optional
        :param s_type: any cwl type
        :return: boolean
        """
        if isinstance(s_type, list) and "null" in s_type:
            return True
        elif isinstance(s_type, str) and s_type.endswith('?'):
            return True
        return False

    def fix_terminal_output_type(self, source_type, sink_type):
        """
        Change type of terminal output in case of mismatch
        :param source_type: any cwl type
        :param sink_type: any cwl type
        :return: any cwl type or none
        """
        optional_output = self.is_optional(sink_type)
        out = deepcopy(sink_type)
        fixed = False
        source_type = self.unpack_list(self.remove_null(source_type))
        sink_type = self.unpack_list(self.remove_null(sink_type))
        if (isinstance(source_type, dict) and source_type["type"] == "array"
                and (not isinstance(sink_type, dict) or
                     sink_type["type"] != "array")):
            out = self.scattered_type(sink_type)
            fixed = True
        elif (isinstance(sink_type, dict) and sink_type["type"] == "array" and
              (not isinstance(source_type, dict) or
               source_type["type"] != "array")):
            out = sink_type["items"]
            fixed = True
        if fixed:
            if optional_output:
                return ["null", out]
            return out
        return None

    def fix_incoming_connections(self, step_id, cwl):
        """
        Fix connections for a workflow step
        :param step_id: string
        :param cwl: dict
        :return: dict
        """
        step = cwl_ensure_dict(cwl['steps'], 'id')[step_id]
        step['in'] = cwl_ensure_dict(step['in'], 'id')
        for step_in_id, step_input in step['in'].items():
            if "valueFrom" in step_input:
                continue
            sink_type = cwl_ensure_dict(
                step['run']['inputs'], 'id'
            ).get(step_in_id, {}).get('type')
            if step_in_id in as_list(step.get('scatter')):
                sink_type = self.scattered_type(sink_type)
            source_type = self.extract_incoming_type(
                as_list(step_input.get('source', [])),
                cwl,
                step_input.get('linkMerge',
                               'merge_nested') == 'merge_flattened'
            )
            if (source_type and sink_type and
                    len(as_list(step_input.get('source', []))) < 2):
                value_from = self.transform_type(source_type, sink_type)
                if value_from:
                    step['in'][step_in_id]['valueFrom'] = value_from
                    msg = ('Added step input valueFrom expression "{}" for '
                           'step {}, for input {}'.format(value_from,
                                                          step_id,
                                                          step_in_id))
                    print('[INFO] - ' + msg)
                    logger.info(msg)
        step['in'] = cwl_ensure_array(step['in'], 'id')
        return step

    def fix_terminal_output_types(self, cwl):
        """
        Fix terminal output types on connection mismatch
        :param cwl: dict
        :return: dict
        """
        if cwl['class'] == 'Workflow':
            steps = cwl_ensure_dict(cwl['steps'], 'id')
            for step_id, step in steps.items():
                if steps[step_id]['run']['class'] == 'Workflow':
                    steps[step_id]['run'] = self.fix_terminal_output_types(
                        steps[step_id]['run']
                    )
            cwl['steps'] = cwl_ensure_array(cwl['steps'], 'id')

            outputs = cwl_ensure_dict(cwl['outputs'], 'id')
            for output_id, output in outputs.items():
                source_type = self.extract_incoming_type(
                    as_list(output.get('outputSource', [])),
                    cwl,
                    output.get('linkMerge',
                               'merge_nested') == 'merge_flattened'
                )
                sink_type = output['type']
                fixed_type = self.fix_terminal_output_type(source_type,
                                                           sink_type)
                if fixed_type:
                    outputs[output_id]['type'] = fixed_type
                    msg = ('Converted terminal output type for {} output '
                           'to {}'.format(output_id, fixed_type))
                    print('[INFO] - ' + msg)
                    logger.info(msg)
            cwl['outputs'] = cwl_ensure_array(outputs, 'id')
        return cwl

    def fix_connection_matching(self, cwl):
        """
        Fix connections in a workflow
        :param cwl: dict
        :return: dict
        """
        if isinstance(cwl, dict) and cwl['class'] == 'Workflow':
            cwl['steps'] = cwl_ensure_dict(cwl['steps'], 'id')
            for step_id in cwl['steps'].keys():
                step = self.fix_incoming_connections(step_id, cwl)
                if step['run']['class'] == 'Workflow':
                    step['run'] = self.fix_connection_matching(step['run'])
                cwl['steps'][step_id] = step
            cwl['steps'] = cwl_ensure_array(cwl['steps'], 'id')
        return cwl
