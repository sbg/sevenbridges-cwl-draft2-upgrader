{
    "cwlVersion": "sbg:draft-2",
    "class": "CommandLineTool",
    "$namespaces": {
        "sbg": "https://sevenbridges.com"
    },
    "id": "withspaces",
    "label": "withspaces",
    "description": "Verify that baseCommand with spaces is converted properly",
    "baseCommand": [
        "sh my_script.sh"
    ],
    "inputs": [],
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
                    "filename": "my_script.sh",
                    "fileContent": "echo 'A test string'"
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
    "arguments": [],
    "stdout": "out.txt"
}