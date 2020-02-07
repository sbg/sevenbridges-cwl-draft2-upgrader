{
    "cwlVersion": "sbg:draft-2",
    "class": "CommandLineTool",
    "$namespaces": {
        "sbg": "https://sevenbridges.com"
    },
    "id": "withbraces",
    "label": "withbraces",
    "description": "Verify that glob with braces is converted properly",
    "baseCommand": ["echo"],
    "inputs": [],
    "outputs": [
        {
            "type": [
                "null",
                "string"
            ],
            "outputBinding": {
                "glob": "{*.bat, *.txt}",
                "loadContents": true,
                "outputEval": {
                    "class": "Expression",
                    "engine": "#cwl-js-engine",
                    "script": "{\n    return $self[0].contents + $self[1].contents\n}"
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
                    "filename": "foo.bat",
                    "fileContent": "Batch"
                },
                {
                    "filename": "foo.txt",
                    "fileContent": "Text"
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
    "arguments": []
}