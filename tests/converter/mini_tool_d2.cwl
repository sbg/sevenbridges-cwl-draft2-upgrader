{
    "cwlVersion": "sbg:draft-2",
    "class": "CommandLineTool",
    "$namespaces": {
        "sbg": "https://sevenbridges.com"
    },
    "id": "minitest",
    "label": "minitest",
    "description": "Take an integer. Return same integer 3 times.",
    "baseCommand": [
        "echo",
        {
            "class": "Expression",
            "engine": "#cwl-js-engine",
            "script": "{\n    return $job.inputs.in\n}"
        }
    ],
    "inputs": [
        {
            "type": [
                "null",
                "int"
            ],
            "inputBinding": {
                "position": 0
            },
            "id": "#in"
        }
    ],
    "outputs": [
        {
            "type": [
                "null",
                "string"
            ],
            "outputBinding": {
                "glob": "out.txt",
                "loadContents": true,
                "outputEval": {
                    "class": "Expression",
                    "engine": "#cwl-js-engine",
                    "script": "{\n    return $self[0].contents\n}"
                }
            },
            "id": "#output"
        }
    ],
    "requirements": [
        {
            "class": "CreateFileRequirement",
            "fileDef": [
                {
                    "filename": {
                        "class": "Expression",
                        "engine": "#cwl-js-engine",
                        "script": "{\n    return \"out2.txt\"\n}"
                    },
                    "fileContent": "1"
                }
            ]
        },
        {
            "id": "#cwl-js-engine",
            "class": "ExpressionEngineRequirement",
            "requirements": [
                {
                    "dockerPull": "rabix/js-engine",
                    "class": "DockerRequirement"
                }
            ]
        }
    ],
    "hints": [
        {
            "class": "sbg:CPURequirement",
            "value": 1
        },
        {
            "class": "sbg:MemRequirement",
            "value": 100
        }
    ],
    "arguments": [
        {
            "position": 0,
            "prefix": "",
            "separate": true,
            "valueFrom": {
                "class": "Expression",
                "engine": "#cwl-js-engine",
                "script": "{\n    return $job.inputs.in\n}"
            }
        }
    ],
    "stdout": "out.txt"
}