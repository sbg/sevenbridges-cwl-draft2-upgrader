import logging
from schema_salad.sourceline import add_lc_filename
from cwltool.validate_js import validate_js_expressions
from cwltool.process import get_schema
import ruamel.yaml

logger = logging.getLogger(__name__)


class CWLValidator:
    """
    Wrap a cwltool functionality to lint JS in an app
    """

    @staticmethod
    def validate_js_expressions_strict(tool: dict):
        """
        Run cwltool function to validate JS in an app
        :param tool: CWL dict
        """
        data = ruamel.yaml.load(ruamel.yaml.dump(tool),
                                ruamel.yaml.RoundTripLoader)
        schema = get_schema(tool['cwlVersion'])[1].names[tool['class']]
        add_lc_filename(data, data.get('label', 'input_document'))
        jshint_options = {
            "includewarnings": [
                "W117",  # <VARIABLE> not defined
                "W104", "W119"  # using ES6 features
            ],
            "strict": "implied",
            "esversion": 5
        }
        validate_js_expressions(data, schema, jshint_options)

    def validate(self, data: dict):
        """
        Validate JS expressions on tool level. For workflows recursively run
        validate_js_expressions_strict on each nested tool.
        :param data: CWL dictionary
        """
        validation_method = self.validate_js_expressions_strict
        if 'class' in data:
            if data['class'] in ['CommandLineTool', 'ExpressionTool']:
                validation_method(data)
            elif data['class'] == 'Workflow':
                if 'steps' in data:
                    for step in data['steps']:
                        if 'run' in step:
                            self.validate(step['run'])
                        else:
                            raise IndexError('Missing run from step.')
            else:
                raise ValueError('Unsupported class name.')

        else:
            raise IndexError('Missing class.')
