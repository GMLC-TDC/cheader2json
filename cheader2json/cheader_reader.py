"""
Copyright (c) 2017-2022,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for
Sustainable Energy, LLC.  See the top-level NOTICE for additional details.
All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
"""

import json
import logging
import os
import sys
from typing import List

import clang.cindex as cidx


class CHeaderParser(object):
    """
    Class that will parse C API headers and create other language bindings

    @ivar parsedInfo: a dictionary with all the parsed cursors in the C API headers

    """

    _types = {}

    def _configureLogger(self, logfilename="clangParserLog.log"):
        self.clangLogger = logging.getLogger(__name__)
        self.clangLogger.setLevel(logging.DEBUG)
        logFormatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        clangLogFileHandler = logging.FileHandler(
            logfilename, mode="w", encoding="utf-8"
        )
        clangLogStreamHandler = logging.StreamHandler()
        clangLogFileHandler.setLevel(logging.DEBUG)
        clangLogFileHandler.setFormatter(logFormatter)
        clangLogStreamHandler.setLevel(logging.INFO)
        clangLogStreamHandler.setFormatter(logFormatter)
        self.clangLogger.addHandler(clangLogFileHandler)
        self.clangLogger.addHandler(clangLogStreamHandler)

    def __init__(self, headers: List[str], ignoredMacros: List[str]):
        """
        Constructor
        """
        CHeaderParser._types["functions"] = {}
        self.parsedInfo = {}
        self.headerFiles = headers
        self._configureLogger()
        self.parseCHeaderFiles(headers, ignoredMacros)

    def _updateTypeFunctionMap(self, dataType: str, spelling: str):
        """
        Updates the types to function map
        """
        if dataType and dataType != "":
            if spelling is None:
                spelling = ""
            if dataType not in CHeaderParser._types.keys():
                CHeaderParser._types[dataType] = [spelling]
            else:
                CHeaderParser._types.get(dataType, []).append(spelling)

    def _addFunctionTypeInfo(self, node: cidx.Cursor, cursorInfoDict: dict):
        """
        Adds type information related to function arguments and return types
        """
        typeKey = ""
        typePointee = None
        if node.kind == cidx.CursorKind.FUNCTION_DECL:
            typeKey = "result_type"
            typePointee = node.result_type
        elif node.kind == cidx.CursorKind.PARM_DECL:
            typeKey = "type"
            typePointee = node.type

        pointer_depth, suffix, typeName = self._getPointerAndTypeInfo(typePointee)

        cursorInfoDict["pointer_depth"] = pointer_depth
        cursorInfoDict["pointer_underlying_type"] = typeName

        if typePointee.kind == cidx.TypeKind.TYPEDEF:
            cursorInfoDict[typeKey] = typeName

        if typePointee.kind == cidx.TypeKind.POINTER:
            if pointer_depth == 2:
                cursorInfoDict[typeKey] = "Double Pointer"
                cursorInfoDict["double_pointer_type"] = typeName + suffix
            else:
                cursorInfoDict["pointer_type"] = typeName + suffix

        self._updateTypeFunctionMap(
            cursorInfoDict.get(typeKey, ""), cursorInfoDict.get("spelling", "")
        )
        self._updateTypeFunctionMap(
            cursorInfoDict.get("pointer_type", ""), cursorInfoDict.get("spelling", "")
        )
        self._updateTypeFunctionMap(
            cursorInfoDict.get("double_pointer_type", ""),
            cursorInfoDict.get("spelling", ""),
        )

    def _getPointerAndTypeInfo(self, typePointee: cidx.Type):
        """
        Gets type name and pointer related information for the given type
        """
        depth = 0
        suffix = "_"
        while typePointee.kind == cidx.TypeKind.POINTER:
            depth += 1
            suffix += "*"
            typePointee = typePointee.get_pointee()
        if typePointee.kind == cidx.TypeKind.ELABORATED:
            typePointee = typePointee.get_named_type()
        return (
            depth,
            suffix,
            (
                typePointee.get_typedef_name()
                if typePointee.kind == cidx.TypeKind.TYPEDEF
                else typePointee.kind.spelling
            ),
        )

    def _isTypeFunctionPointer(self, node: cidx.Cursor) -> bool:
        if (
            node.kind == cidx.CursorKind.TYPEDEF_DECL
            or node.type.kind == cidx.TypeKind.TYPEDEF
        ):
            if node.underlying_typedef_type.kind == cidx.TypeKind.POINTER:
                type_pointee = node.underlying_typedef_type.get_pointee()
                if type_pointee.kind == cidx.TypeKind.FUNCTIONPROTO:
                    return True
        elif node.type.kind == cidx.TypeKind.POINTER:
            type_pointee = node.type.get_pointee()
            if type_pointee.kind == cidx.TypeKind.FUNCTIONPROTO:
                return True
        return False

    def _getFunctionPointerArguments(self, node: cidx.Cursor) -> list:
        # Returns a list of objects with info on function pointer arguments
        function_pointer_arguments = []
        for arg in node.get_children():
            arg_info = {
                "name": arg.spelling,
                "type": arg.type.spelling
                if arg.kind != cidx.TypeKind.ELABORATED
                else arg.get_named_type().spelling,
            }
            if self._isTypeFunctionPointer(arg):
                arg_info["function_pointer_arguments"] = (
                    self._getFunctionPointerArguments(arg)
                )
                arg_info["function_pointer_result_type"] = (
                    arg.type.get_pointee().get_result().spelling
                )
            function_pointer_arguments.append(arg_info)
        return function_pointer_arguments

    def _cursorInfo(self, node: cidx.Cursor) -> dict:
        """
        Helper function for parseCHeaderFiles()
        """
        cursorInfoDict = {
            "kind": node.kind.name,
            "spelling": node.spelling,
            "location": node.location.file.name,
            "type": node.type.kind.spelling
            if node.type.kind != cidx.TypeKind.ELABORATED
            else node.type.get_named_type().spelling,
            "result_type": node.result_type.kind.spelling
            if node.result_type.kind != cidx.TypeKind.ELABORATED
            else node.result_type.get_named_type().spelling,
            "brief_comment": node.brief_comment,
        }

        cursor_range = node.extent
        cursorInfoDict["start_line"] = cursor_range.start.line
        cursorInfoDict["end_line"] = cursor_range.end.line
        if node.kind == cidx.CursorKind.FUNCTION_DECL:
            cursorInfoDict["raw_comment"] = node.raw_comment
            self._addFunctionTypeInfo(node, cursorInfoDict)
            cursorInfoDict["arguments"] = {}
            argNum = 0
            for arg in node.get_arguments():
                cursorInfoDict["arguments"][argNum] = self._cursorInfo(arg)
                argNum += 1
            cursorInfoDict["argument_count"] = argNum
            CHeaderParser._types["functions"][cursorInfoDict.get("spelling", "")] = (
                cursorInfoDict["arguments"]
            )
        if node.kind == cidx.CursorKind.PARM_DECL:
            self._addFunctionTypeInfo(node, cursorInfoDict)
        if (
            node.kind == cidx.CursorKind.TYPEDEF_DECL
            or node.type.kind == cidx.TypeKind.TYPEDEF
        ):
            cursorInfoDict["type"] = node.underlying_typedef_type.spelling
            if cursorInfoDict["type"] == "":
                cursorInfoDict["type"] = node.type.get_typedef_name()
            if self._isTypeFunctionPointer(node):
                cursorInfoDict["function_pointer_arguments"] = (
                    self._getFunctionPointerArguments(node)
                )
                cursorInfoDict["function_pointer_result_type"] = (
                    node.underlying_typedef_type.get_pointee().get_result().spelling
                )
        if node.kind == cidx.CursorKind.ENUM_DECL:
            cursorInfoDict["enumerations"] = {}
            enumNum = 0
            for i in node.get_children():
                cursorInfoDict["enumerations"][enumNum] = self._cursorInfo(i)
                enumNum += 1
        if node.kind == cidx.CursorKind.ENUM_CONSTANT_DECL:
            cursorInfoDict["value"] = node.enum_value
        if node.kind == cidx.CursorKind.VAR_DECL:
            tokens = []
            for t in node.get_tokens():
                tokens.append(t.spelling)
            if tokens[len(tokens) - 2] == "-":
                value = tokens[len(tokens) - 2] + tokens[len(tokens) - 1]
            else:
                value = tokens[len(tokens) - 1]
            try:
                cursorInfoDict["value"] = json.loads(value)
            except json.decoder.JSONDecodeError:
                cursorInfoDict["value"] = value
        if node.kind == cidx.CursorKind.STRUCT_DECL:
            cursorInfoDict["members"] = {}
            memberNum = 0
            for i in node.get_children():
                cursorInfoDict["members"][memberNum] = self._cursorInfo(i)
                memberNum += 1
        if node.kind == cidx.CursorKind.MACRO_DEFINITION:
            value = ""
            for t in node.get_tokens():
                value = t.spelling
            try:
                cursorInfoDict["value"] = json.loads(value)
            except json.decoder.JSONDecodeError:
                cursorInfoDict["value"] = value
        return cursorInfoDict

    def parseCHeaderFiles(self, headers: List[str], ignoredMacros: List[str]) -> None:
        """
        Function that parses the C header files
        @param headers: A list of the C header files to parse
        @param ignoredMacros: A list of macros to ignore
        """
        idx = cidx.Index.create()
        cursorNum = 0
        for headerFile in headers:
            tu = idx.parse(
                headerFile,
                options=cidx.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD,
            )
            for c in tu.cursor.get_children():
                if c.location.file is not None:
                    if (
                        c.location.file.name == headerFile
                        and c.displayname not in ignoredMacros
                    ):
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
        self.clangLogger.info("Clang successfully parsed the C header files!")
        self.clangLogger.debug(
            f"The clang parser result:\n"
            f"{json.dumps(self.parsedInfo, indent=4, sort_keys=True)}\n"
            f"{json.dumps(CHeaderParser._types, indent=4, sort_keys=True)}"
        )
