import json
from argparse import ArgumentParser
from typing import Any, ClassVar, Dict, List

import clang.cindex as cidx


class CHeaderParser(object):
    """
    Class that will parse the C API headers and create a JSON file for generating other
    language bindings

    @ivar parsedInfo: a dictionary containing all the parsed cursors found in the C API
    headers

    """

    _types = {}
    parsedInfo: dict  # Dictionary of parsed value

    def __init__(self, cHeaders: List[str]):
        """
        Constructor
        """
        self._types["functions"] = {}
        self.parsedInfo = {}
        self.parseCHeaderFiles(cHeaders)

    def _cursorInfo(self, node: cidx.Cursor) -> dict():
        """
        Helper function for parseCHeaderFiles()
        """
        cursorInfoDict = {
            "kind": node.kind.name,
            "spelling": node.spelling,
            "location": node.location.file.name,
            "type": node.type.kind.spelling,
            "result_type": node.result_type.kind.spelling,
            "brief_comment": node.brief_comment,
        }
        cursor_range = node.extent
        cursorInfoDict["start_line"] = cursor_range.start.line
        cursorInfoDict["end_line"] = cursor_range.end.line
        if node.kind == cidx.CursorKind.FUNCTION_DECL:
            cursorInfoDict["raw_comment"] = node.raw_comment
            if node.result_type.kind == cidx.TypeKind.POINTER:
                pointerType = node.result_type.get_pointee()
                if pointerType.kind == cidx.TypeKind.POINTER:
                    cursorInfoDict["result_type"] = "Double Pointer"
                    cursorInfoDict["double_pointer_type"] = (
                        pointerType.get_pointee().kind.spelling + "_**"
                    )
                else:
                    cursorInfoDict["pointer_type"] = pointerType.kind.spelling + "_*"
            if node.result_type.kind == cidx.TypeKind.TYPEDEF:
                cursorInfoDict["result_type"] = node.result_type.get_typedef_name()
            if cursorInfoDict.get("result_type", "") != "":
                if cursorInfoDict.get("result_type", "") not in self._types.keys():
                    self._types[cursorInfoDict.get("result_type", "")] = [
                        cursorInfoDict.get("spelling", "")
                    ]
                else:
                    self._types.get(cursorInfoDict.get("result_type", ""), []).append(
                        cursorInfoDict.get("spelling", "")
                    )
            if cursorInfoDict.get("pointer_type", "") != "":
                if cursorInfoDict.get("pointer_type", "") not in self._types.keys():
                    self._types[cursorInfoDict.get("pointer_type", "")] = [
                        cursorInfoDict.get("spelling", "")
                    ]
                else:
                    self._types.get(cursorInfoDict.get("pointer_type", ""), []).append(
                        cursorInfoDict.get("spelling", "")
                    )
            if cursorInfoDict.get("double_pointer_type", "") != "":
                if (
                    cursorInfoDict.get("double_pointer_type", "")
                    not in self._types.keys()
                ):
                    self._types[cursorInfoDict.get("double_pointer_type", "")] = [
                        cursorInfoDict.get("spelling", "")
                    ]
                else:
                    self._types.get(
                        cursorInfoDict.get("double_pointer_type", ""), []
                    ).append(cursorInfoDict.get("spelling", ""))
            cursorInfoDict["arguments"] = {}
            argNum = 0
            for arg in node.get_arguments():
                cursorInfoDict["arguments"][argNum] = self._cursorInfo(arg)
                argNum += 1
            self._types["functions"][
                cursorInfoDict.get("spelling", "")
            ] = cursorInfoDict["arguments"]
        if node.kind == cidx.CursorKind.PARM_DECL:
            if node.type.kind == cidx.TypeKind.TYPEDEF:
                cursorInfoDict["type"] = node.type.get_typedef_name()
            if node.type.kind == cidx.TypeKind.POINTER:
                typePointee = node.type.get_pointee()
                if typePointee.kind == cidx.TypeKind.TYPEDEF:
                    cursorInfoDict["pointer_type"] = (
                        typePointee.get_typedef_name() + "_*"
                    )
                elif typePointee.kind == cidx.TypeKind.POINTER:
                    cursorInfoDict["type"] = "Double Pointer"
                    cursorInfoDict["double_pointer_type"] = (
                        typePointee.get_pointee().kind.spelling + "_**"
                    )
                else:
                    cursorInfoDict["pointer_type"] = typePointee.kind.spelling + "_*"
            if cursorInfoDict.get("type", "") != "":
                if cursorInfoDict.get("type", "") not in self._types.keys():
                    self._types[cursorInfoDict.get("type", "")] = [
                        cursorInfoDict.get("spelling", "")
                    ]
                else:
                    self._types.get(cursorInfoDict.get("type", ""), []).append(
                        cursorInfoDict.get("spelling", "")
                    )
            if cursorInfoDict.get("pointer_type", "") != "":
                if cursorInfoDict.get("pointer_type", "") not in self._types.keys():
                    self._types[cursorInfoDict.get("pointer_type", "")] = [
                        cursorInfoDict.get("spelling", "")
                    ]
                else:
                    self._types.get(cursorInfoDict.get("pointer_type", ""), []).append(
                        cursorInfoDict.get("spelling", "")
                    )
            if cursorInfoDict.get("double_pointer_type", "") != "":
                if (
                    cursorInfoDict.get("double_pointer_type", "")
                    not in self._types.keys()
                ):
                    self._types[cursorInfoDict.get("double_pointer_type", "")] = [
                        cursorInfoDict.get("spelling", "")
                    ]
                else:
                    self._types.get(
                        cursorInfoDict.get("double_pointer_type", ""), []
                    ).append(cursorInfoDict.get("spelling", ""))
        if (
            node.kind == cidx.CursorKind.TYPEDEF_DECL
            or node.type.kind == cidx.TypeKind.TYPEDEF
        ):
            cursorInfoDict["type"] = node.underlying_typedef_type.spelling
            if cursorInfoDict["type"] == "":
                cursorInfoDict["type"] = node.type.get_typedef_name()
        if node.kind == cidx.CursorKind.ENUM_DECL:
            cursorInfoDict["enumerations"] = {}
            enumNum = 0
            for i in node.get_children():
                cursorInfoDict["enumerations"][enumNum] = self._cursorInfo(i)
                enumNum += 1
        if node.kind == cidx.CursorKind.ENUM_CONSTANT_DECL:
            cursorInfoDict["value"] = node.enum_value
        if node.kind == cidx.CursorKind.VAR_DECL:
            value = ""
            for t in node.get_tokens():
                value = t.spelling
            cursorInfoDict["value"] = json.loads(value)
        if node.kind == cidx.CursorKind.STRUCT_DECL:
            cursorInfoDict["members"] = {}
            memberNum = 0
            for i in node.get_children():
                cursorInfoDict["members"][memberNum] = self._cursorInfo(i)
                memberNum += 1
        return cursorInfoDict

    def parseCHeaderFiles(self, cHeaders: List[str]) -> None:
        """
        Function that parses the C header files
        @param cHeaders: A list of the C header files to parse
        """
        idx = cidx.Index.create()
        cursorNum = 0
        for headerFile in cHeaders:
            tu = idx.parse(headerFile)
            for c in tu.cursor.get_children():
                if c.location.file.name == headerFile:
                    self.parsedInfo[cursorNum] = self._cursorInfo(c)
                    cursorNum += 1
            deletekeys = []
            for key in self.parsedInfo.keys():

                if self.parsedInfo[key]["spelling"] == "":
                    for i in self.parsedInfo.keys():
                        if i != key:
                            if (
                                self.parsedInfo[key]["start_line"]
                                == self.parsedInfo[i]["start_line"]
                                and self.parsedInfo[key]["end_line"]
                                == self.parsedInfo[i]["end_line"]
                            ):
                                self.parsedInfo[key]["spelling"] = self.parsedInfo[i][
                                    "spelling"
                                ]
                                deletekeys.append(i)
            for key in deletekeys:
                del self.parsedInfo[key]


def main(cHeaders: List[str]) -> None:
    """
    Main function for parsing C header files and dumping the parsed info as a JSON file
    """
    cheaderParser = CHeaderParser(cHeaders)
    with open("parsedHeaderDict.json", "w") as pFile:
        pFile.write(json.dumps(cheaderParser.parsedInfo, indent=4, sort_keys=True))
        pFile.write(json.dumps(cheaderParser._types, indent=4, sort_keys=True))
    print("c headers parsed successfully!")


if __name__ == "__main__":
    userInputParser = ArgumentParser()
    userInputParser.add_argument(
        "headers", default=[], nargs="+", help="list of c header files to parse"
    )
    userArgs = userInputParser.parse_args()
    main(userArgs.headers)
