from typing import Dict, List, Union


def fix_glob_with_brace(cwl: Union[List, Dict]):
    if isinstance(cwl, list):
        return [fix_glob_with_brace(_v) for _v in cwl]

    if isinstance(cwl, dict):
        if "glob" in cwl:
            _glob = cwl.get("glob")
            if isinstance(_glob, str):
                if _glob.startswith("{") and _glob.endswith("}"):
                    cwl["glob"] = [_s.strip() for _s in _glob[1:-1].split(",")]

        return {_k: fix_glob_with_brace(_v) for _k, _v in cwl.items()}

    return cwl
