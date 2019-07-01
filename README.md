# SevenBridges CWL Draft2 Upgrader (BETA)

SevenBridges CWL Draft2 Upgrader is a Python3 package that comes with three command line tools:
- `sbg_cwl_upgrader`
- `sbg_cwl_decomposer`
- `sbg_validate_js_cwl_v1`

Command line tool `sbg_cwl_upgrader` allows you to upgrade CWL 
tools and workflows written in sbg:draft-2 to CWL v1.0. The source CWL can be on your local machine or on the Seven Bridges platform and the
converted CWL can be output to your local machine or onto the Seven Bridges platform. For more details see [this section](#recommended-draft2-to-cwl10-upgrade-flow).  
Note that the conversion process is semi-automated, manual intervention may be required. For more details see the [known limitations section](#known-limitations).  
Manual part of the conversion process may be tedious and require changes to the CWL code. Therefore, strong understanding of the CWL syntax is desirable.

Command line tool `sbg_cwl_decomposer` installs individual components of a workflow and re-links them back in the workflow. For more details see the [usage section](#decompose-a-platform-workflow).

Command line tool `sbg_validate_js_cwl_v1` checks a CWL document for non-strict syntax in JavaScript expressions and produces warnings. For more details see the [usage section](#checking-javascript-version-compatibility-in-expressions).

## Installation

This tool requires Python3. In general, it is helpful to install user space
Python applications in [virtual environments][venv].

### Install using pip 

[venv]: https://packaging.python.org/guides/installing-using-pip-and-virtualenv/

The package can be installed with `pip`, using

```
python3 -m pip install sevenbridges-cwl-draft2-upgrader
```

### Install from source code

Install from source by cloning the repo, using
```
git clone git@github.com:sbg/sevenbridges-cwl-draft2-upgrader.git
python3 -m pip install ./sevenbridges-cwl-draft2-upgrader
```

## Usage

Package commands use Platform authentication by reading default config from 
the `~/.sevenbridges/credentials` file.
For additional ways of providing authentication, please consult `sbg_cwl_upgrader --help`.

### Save upgraded CWL to a local file
As an example, we'll take a publicly available workflow on the Seven Bridges platform, the
GATK4 WES workflow, convert it to CWL1.0 and save it locally:
```
sbg_cwl_upgrader -i admin/sbg-public-data/whole-exome-sequencing-bwa-gatk-4-0 -o wes.cwl
```

The arguments to `-i` and `-o` are interpreted as local CWL files if they end
in `.cwl`, `.yml`, `.yaml`, or `.json` and Apps on the Seven Bridges platform otherwise.

### Save upgraded CWL to a Platform project
We can also directly upload the converted CWL1.0 workflow to the Platform:
```
sbg_cwl_upgrader -i admin/sbg-public-data/whole-exome-sequencing-bwa-gatk-4-0 -o username/usernames-demo-project/wes
```
You will additionally be asked if you want to decompose the workflow after installation. 

### Decompose a Platform workflow
Sometimes, you want all workflow components to be available in the same project as the workflow. This can be done using the `sbg_cwl_decomposer` tool.  
This tool will:
- Find all component tools of a workflow
- Install them in the project where the workflow is installed
- Insert them in the workflow so they are editable in that project

Example command:
```
sbg_cwl_decomposer -a username/usernames-demo-project/wes
```

### Decompose a local workflow
Sometimes, you want all workflow components to be available under the `steps` folder, next to the main workflow. This can be done using the `sbg_cwl_decomposer` tool.  
This tool will:
- Find all component tools of a workflow
- Install them in the `steps` folder alongside the main workflow
- Insert them in the workflow as strings (relative paths to the main workflow)

Example command:
```
sbg_cwl_decomposer -a workflow.cwl
```

## Recommended draft2 to CWL1.0 upgrade flow

### Convert a Platform draft2 workflow to CWL1.0 and run it on the Seven Bridges Platform

- Prepare a development project and copy the workflow there.
- Run a task in the development project with the draft2 workflow.
- Run the upgrader script with the same app ID for `-i` and `-o` parameters to create a new revision over the draft2 wf:  
`sbg_cwl_upgrader -i <app_id> -o <app_id> -d -u`.
- This will upgrade the workflow and the tools/subworkflows, and install them in the project as separate apps.
- Rerun the task that used the draft2 workflow with the same inputs.
- Debug failures. Consult the [known limitations section](#known-limitations) and do a manual intervention
- If a tool in the workflow requires modifications, find the tool in the project, apply a fix there, and update the tool in the workflow. Good practice is to test the modified tool individually before updating in the workflow.
- Once the CWL1.0 task completes, check if all the expected outputs are produced properly.

### Convert a Platform draft2 workflow to CWL1.0 and run it using cwltool

- Run the upgrader script with the `-o` parameter pointing to a local file:  
`sbg_cwl_upgrader -i <app_id> -o /path/to/app.cwl -d -v`.
- This will upgrade the workflow and the tools/subworkflows, and install them in the `steps` folder alongside the main workflow.
- Validate JS expressions in the workflow - [check this section](#checking-javascript-version-compatibility-in-expressions).
- Validate the workflow with `cwltool --validate /path/to/app.cwl` and check for potential errors - see the [portability notes](#portability-notes) section.
- Prepare workflow inputs for local execution and describe them in `<name>_inputs.json` file (can be either JSON or YAML).
- Run with cwltool using `cwltool /path/to/app.cwl <name>_inputs.json`.
- Debug failures. Consult the [known limitations section](#known-limitations) and do a manual intervention.
- If a tool in the workflow requires modifications, find the tool in the `steps` folder, apply a fix there, and rerun the workflow. Good practice is to test the modified tool individually before updating in the workflow.
- Once the CWL1.0 task completes, check if all the expected outputs are produced properly.


## Known limitations

### Conversion notes
The conversion process is semi-automated, meaning some differences between CWL versions can't be automatically resolved and require manual intervention.
Manual intervention may be required when:
- Tool parses the `job.json` file, which is a Seven Bridges Platform specific log file. This should be avoided in tools.
- File in `InitialWorkdirRequirement` is created in a subfolder, e.g. `entryname: foo/bar`. Files need to be created directly in the working directory.
- Glob is catching files outside the working directory, e.g. `glob: $(inputs.input.path)`. In CWL, every job has its own working directory in order to keep things clean. Glob should only capture files inside the working directory (meaning tools should only write outputs in the working directory).
- JS expression is missing a `return` statement. Every expression should return something (at least `null`), and must use `return`.
- JS expression is editing the `inputs` variable and then accessing it. The tool converts `$job.inputs` to `inputs`, so in CWL1.0 JS expressions should no longer redefine the `inputs` variable.
- The converter is not fully tested on upgrading mixed-version workflows. 

### Portability notes
The CWL standard specifies that glob patterns must follow POSIX(3) pattern matching and JS expressions should follow ES5.1 strict syntax. The Seven Bridges platform allows some additional features for glob and JS, which may not work on executors that strictly follow the CWL standard. Common examples include:  
- Glob pattern with brace expand syntax [not capturing outputs in cwltool](https://github.com/common-workflow-language/cwltool/issues/870), e.g. `glob: {*.txt,*.pdf}`. Using brace expand pattern (curly brackets) is a bash extension to the glob specification. This pattern will work on the Seven Bridges platform, but not with cwltool.  
To get this glob working with all executors, break down the single string pattern into a list of string patterns, i.e. convert `glob: "{*.txt,*.pdf}"` to `glob: ["*.txt","*.pdf"]`
- Some CWL executors require strict type matching between connected ports, e.g. a `File` object can't connect to a `File[]` input and vice versa.  
These connection mismatches can be handled by adding a step input `valueFrom` expression to transform a `File` to `File[]` with `valueFrom: $([self])`, or transform `File[]` to `File` with `valueFrom: $(self[0])`.
- Some CWL executors require Javascript expressions to be written in ES5.1 strict mode (more info [here](#note-on-javascript-versions-in-expressions)).

### Note on Javascript versions in expressions

While the Seven Bridges platform executor correctly evaluates both [JS ES6 and JS ES5.1][js-ver]
code in expressions, some CWL executors only evaluate JS ES5.1 in strict mode. If a converted 
workflow contains JS ES6 or JS with non-strict syntax, the workflow may not be executable on all executors.  

[js-ver]: https://www.w3schools.com/js/js_versions.asp  

### Checking Javascript version compatibility in expressions

Preliminary validation of JS expressions in an app can be done using the `sbg_validate_js_cwl_v1` tool. Running the command:  
```
sbg_validate_js_cwl_v1  -i app.cwl
```
will write the expression evaluation result to the stderr stream.  
To get a list of undeclared variables without duplicates, run:
```
sbg_validate_js_cwl_v1 -i app.cwl 2>&1 >/dev/null | awk 'NR % 3 == 0' | uniq
```
and add `var` to the first instances of all undeclared variables.
