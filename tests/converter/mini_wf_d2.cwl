{
  "class": "Workflow",
  "cwlVersion": "sbg:draft-2",
  "id": "wf1",
  "label": "wf1",
  "$namespaces": {
    "sbg": "https://www.sevenbridges.com/"
  },
  "inputs": [
    {
      "type": [
        {
          "type": "array",
          "items": "string"
        }
      ],
      "id": "#input",
      "sbg:includeInPorts": true,
      "sbg:x": -316.39886474609375,
      "sbg:y": -144
    }
  ],
  "outputs": [
    {
      "id": "#output",
      "source": [
        "#t2.output"
      ],
      "type": [
        "string"
      ],
      "sbg:x": 317.60113525390625,
      "sbg:y": -89
    }
  ],
  "steps": [
    {
      "id": "#t1",
      "inputs": [
        {
          "id": "#t1.input",
          "source": [
            "#input"
          ]
        }
      ],
      "outputs": [
        {
          "id": "#t1.output"
        }
      ],
      "run": {
        "cwlVersion": "sbg:draft-2",
        "class": "CommandLineTool",
        "$namespaces": {
          "sbg": "https://www.sevenbridges.com/"
        },
        "id": "t1",
        "label": "t1",
        "baseCommand": [
          {
            "class": "Expression",
            "engine": "#cwl-js-engine",
            "script": "{\n    return \"echo \" + $job.inputs.input[0]\n\n}"
          }
        ],
        "inputs": [
          {
            "type": [
              {
                "type": "array",
                "items": "string"
              }
            ],
            "inputBinding": {
              "position": 0
            },
            "id": "#input"
          }
        ],
        "outputs": [
          {
            "type": [
              "null",
              "File"
            ],
            "outputBinding": {
              "glob": "a.txt"
            },
            "id": "#output"
          }
        ],
        "requirements": [
          {
            "class": "ExpressionEngineRequirement",
            "id": "#cwl-js-engine",
            "requirements": [
              {
                "class": "DockerRequirement",
                "dockerPull": "rabix/js-engine"
              }
            ]
          }
        ],
        "stdout": "a.txt"
      },
      "label": "t1",
      "sbg:x": -95.3984375,
      "sbg:y": -68
    },
    {
      "id": "#t2",
      "inputs": [
        {
          "id": "#t2.input",
          "source": "#t1.output"
        }
      ],
      "outputs": [
        {
          "id": "#t2.output"
        }
      ],
      "run": {
        "cwlVersion": "sbg:draft-2",
        "class": "CommandLineTool",
        "$namespaces": {
          "sbg": "https://www.sevenbridges.com/"
        },
        "id": "t2",
        "label": "t2",
        "baseCommand": [
          "ls"
        ],
        "inputs": [
          {
            "sbg:stageInput": "copy",
            "type": [
              "File"
            ],
            "inputBinding": {
              "position": 0,
              "secondaryFiles": [

              ]
            },
            "id": "#input"
          }
        ],
        "outputs": [
          {
            "type": [
              "string"
            ],
"outputBinding": {
              "glob": "a.txt",
              "loadContents": true,
              "outputEval": {
                "class": "Expression",
                "engine": "#cwl-js-engine",
                "script": "{\n    return self[0].contents\n}"
              }
            },
            "id": "#output"
          }
        ]
      },
      "label": "t2",
      "sbg:x": 136.60113525390625,
      "sbg:y": -43
    }
  ]
}