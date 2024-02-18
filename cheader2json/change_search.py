def findAll(ast, kindtype):
    items = []
    for val in ast.values():
        if val["kind"] == kindtype:
            items.append(val)
    return items

def findAllWithStartLine(ast, kindtype, startline):
    items = []
    for val in ast.values():
        if val["kind"] == kindtype:
            if val["start_line"] == startline:
                items.append(val)
    return items

def findUnknownKinds(ast):
    knowntypes = ["FUNCTION_DECL", "TYPEDEF_DECL", "ENUM_DECL", "VAR_DECL", "STRUCT_DECL", "MACRO_DEFINITION", "MACRO_INSTANTIATION", "INCLUSION_DIRECTIVE"]
    knownsubtypes = ["PARM_DECL", "ENUM_CONSTANT_DECL", "FIELD_DECL"]
    for val in ast.values():
        if val["kind"] not in knowntypes:
            print(f"Unknown Kind Type: {val['kind']}")

def diffAst(old_ast, new_ast):
    # FUNCTION_DECL
    old_functions = {}
    for v in findAll(old_ast, "FUNCTION_DECL"):
        old_functions[v["spelling"]] = v

    new_functions = {}
    for v in findAll(new_ast, "FUNCTION_DECL"):
        new_functions[v["spelling"]] = v

    for f in new_functions:
        if not f in old_functions:
            first_arg = True
            args_str = ''
            for v in findAll(new_functions[f]["arguments"], "PARM_DECL"):
                if not first_arg:
                    args_str += ', '
                args_str += v['pointer_underlying_type']
                for i in range(0, v['pointer_depth']):
                    args_str += '*'
                args_str += ' ' + v['spelling']
                first_arg = False
            print(f"New function: {f} ({args_str})")
    for f in old_functions:
        if not f in new_functions:
            print(f"Removed function: {f}")
    for f in new_functions:
        if f in old_functions:
            if new_functions[f]["result_type"] != old_functions[f]["result_type"]:
                print(f"Changed return type in {f} from {old_functions[f]['result_type']} to {new_functions[f]['result_type']}")
            if "pointer_type" in new_functions[f]:
                if new_functions[f]["pointer_type"] != old_functions[f]["pointer_type"]:
                    print(f"Changed return pointer type in {f} from {old_functions[f]['pointer_type']} to {new_functions[f]['pointer_type']}")
            if "double_pointer_type" in new_functions[f]:
                if new_functions[f]["double_pointer_type"] != old_functions[f]["double_pointer_type"]:
                    print(f"Changed return double pointer type in {f} from {old_functions[f]['double_pointer_type']} to {new_functions[f]['double_pointer_type']}")

    # function["arguments"] -> PARM_DECL
    for k in new_functions:
        f_new = new_functions[k]
        if k in old_functions:
            f_old = old_functions[k]
            if len(f_old["arguments"]) != len(f_new["arguments"]):
                # the number of arguments doesn't match, something was added or removed
                old_parms = {}
                for v in findAll(f_old["arguments"], "PARM_DECL"):
                    old_parms[v["spelling"]] = v
                new_parms = {}
                for v in findAll(f_new["arguments"], "PARM_DECL"):
                    new_parms[v["spelling"]] = v
                for p in new_parms:
                    if not p in old_parms:
                        print(f"New parameter {p} added to function {k}")
                for p in old_parms:
                    if not p in new_parms:
                        print(f"Removed parameter {p} from function {k}")
            else:
                # check if the same arguments appear in the same order
                for parm_k in f_new["arguments"].keys():
                    new_parm = f_new["arguments"][parm_k]
                    old_parm = f_old["arguments"][parm_k]
                    if new_parm["type"] != old_parm["type"]:
                        print(f"Changed type for parm {new_parm['spelling']} in {k} from {old_parm['type']} to {new_parm['type']}")
                    # pointer_type
                    if "pointer_type" in new_parm:
                        if new_parm["pointer_type"] != old_parm["pointer_type"]:
                            print(f"Changed pointer type for parm {new_parm['spelling']} in {k} from {old_parm['pointer_type']} to {new_parm['pointer_type']}")
                    # double_pointer_type
                    if "double_pointer_type" in new_parm:
                        if new_parm["double_pointer_type"] != old_parm["double_pointer_type"]:
                            print(f"Changed double pointer type for parm {new_parm['spelling']} in {k} from {old_parm['double_pointer_type']} to {new_parm['double_pointer_type']}")

            # TODO may be better not to construct these new lists and instead iterate by keys() using findAll results
            old_parms = {}
            for v in findAll(f_old["arguments"], "PARM_DECL"):
                old_parms[v["spelling"]] = v
            new_parms = {}
            for v in findAll(f_new["arguments"], "PARM_DECL"):
                new_parms[v["spelling"]] = v
            for p in new_parms:
                if not p in old_parms:
                    print(f"New parameter {p} added to function {k}")
            for p in old_parms:
                if not p in new_parms:
                    print(f"Removed parameter {p} from function {k}")
            for p in new_parms:
                if p in old_parms:
                    # Parameter order matters, so should iterate through both parameter lists in order and compare
                    pass

    # TYPEDEF_DECL
    old_typedefs = {}
    for v in findAll(old_ast, "TYPEDEF_DECL"):
        old_typedefs[v["spelling"]] = v

    new_typedefs = {}
    for v in findAll(new_ast, "TYPEDEF_DECL"):
        new_typedefs[v["spelling"]] = v

    for t in new_typedefs:
        if not t in old_typedefs:
            print(f"New typedef: {t}")
    for t in old_typedefs:
        if not t in new_typedefs:
            print(f"Removed typedef: {t}")
    # TYPEDEF

    # ENUM_DECL
    old_enums = {}
    for v in findAll(old_ast, "ENUM_DECL"):
        old_enums[v["spelling"]] = v

    new_enums = {}
    for v in findAll(new_ast, "ENUM_DECL"):
        new_enums[v["spelling"]] = v

    for e in new_enums:
        if not e in old_enums:
            print(f"New enum: {e}")
    for e in old_enums:
        if not e in new_enums:
            print(f"Removed enum: {e}")

    # enum["enumerations"] -> ENUM_CONSTANT_DECL
    for k in new_enums:
        v_new = new_enums[k]
        if k in old_enums:
            v_old = old_enums[k]
            old_constants = {}
            for v in findAll(v_old["enumerations"], "ENUM_CONSTANT_DECL"):
                old_constants[v["spelling"]] = v
            new_constants = {}
            for v in findAll(v_new["enumerations"], "ENUM_CONSTANT_DECL"):
                new_constants[v["spelling"]] = v
            for c in new_constants:
                if not c in old_constants:
                    print(f"New constant {c}={new_constants[c]['value']} in enum {k}")
            for c in old_constants:
                if not c in new_constants:
                    print(f"Removed constant {c} from enum {k}")
            for c in new_constants:
                if c in old_constants:
                    if new_constants[c]["value"] != old_constants[c]["value"]:
                        print(f"Value of constant {c} in enum {k} changed from {old_constants[c]['value']} to {new_constants[c]['value']}")
                    if new_constants[c]["type"] != old_constants[c]["type"]:
                        print(f"Type of constant {c} in enum {k} changed from {old_constants[c]['type']} to {new_constants[c]['type']}")

    # VAR_DECL
    old_vars = {}
    for v in findAll(old_ast, "VAR_DECL"):
        old_vars[v["spelling"]] = v

    new_vars = {}
    for v in findAll(new_ast, "VAR_DECL"):
        new_vars[v["spelling"]] = v

    for v in new_vars:
        if not v in old_vars:
            print(f"New var: {v}")
    for v in old_vars:
        if not v in new_vars:
            print(f"Removed var: {v}")

    # STRUCT_DECL
    old_structs = {}
    for v in findAll(old_ast, "STRUCT_DECL"):
        old_structs[v["spelling"]] = v

    new_structs = {}
    for v in findAll(new_ast, "STRUCT_DECL"):
        new_structs[v["spelling"]] = v

    for s in new_structs:
        if not s in old_structs:
            print(f"New struct: {s}")
    for s in old_structs:
        if not s in new_structs:
            print(f"Removed struct: {s}")
    # struct["members"] -> FIELD_DECL

    for k in new_structs:
        s_new = new_structs[k]
        if k in old_structs:
            s_old = old_structs[k]
            old_fields = {}
            for v in findAll(s_old["members"], "FIELD_DECL"):
                old_fields[v["spelling"]] = v
            new_fields = {}
            for v in findAll(s_new["members"], "FIELD_DECL"):
                new_fields[v["spelling"]] = v
            for f in new_fields:
                if not f in old_fields:
                    print(f"New field {f} in struct {k}")
            for f in old_fields:
                if not f in new_fields:
                    print(f"Removed field {f} from struct {k}")
            for f in new_fields:
                if f in old_fields:
                    if new_fields[f]["type"] != old_fields[f]["type"]:
                        print(f"Type of field {f} in struct {k} changed from {old_fields[f]['type']} to {new_fields[f]['type']}")

    # MACRO_DEFINITION
    old_macros = {}
    for v in findAll(old_ast, "MACRO_DEFINITIONS"):
        old_macros[v["spelling"]] = v

    new_macros = {}
    for v in findAll(new_ast, "MACRO_DEFINITIONS"):
        new_macros[v["spelling"]] = v

    for m in new_macros:
        if not m in old_macros:
            print(f"New macro: {m}")
    for m in old_macros:
        if not f in new_macros:
            print(f"Removed macro: {m}")

    # MACRO_INSTANTIATION
    old_deprecated_functions = {}
    for v in findAll(old_ast, "MACRO_INSTANTIATION"):
        if v["spelling"] == "HELICS_DEPRECATED":
            for vf in findAllWithStartLine(old_ast, "FUNCTION_DECL", v["start_line"]):
                old_deprecated_functions[vf["spelling"]] = vf

    new_deprecated_functions = {}
    for v in findAll(new_ast, "MACRO_INSTANTIATION"):
        if v["spelling"] == "HELICS_DEPRECATED":
            for vf in findAllWithStartLine(new_ast, "FUNCTION_DECL", v["start_line"]):
                new_deprecated_functions[vf["spelling"]] = vf

    for f in new_deprecated_functions:
        if not f in old_deprecated_functions:
            print(f"New deprecated function: {f}")
    for f in old_deprecated_functions:
        if not f in new_deprecated_functions:
            print(f"Removed deprecated function: {f}")

    # INCLUSION_DIRECTIVE

    findUnknownKinds(new_ast)
