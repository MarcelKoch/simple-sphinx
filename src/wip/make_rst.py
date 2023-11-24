#!/usr/bin/env python3
import argparse
import dataclasses as dc
import json
import random
import sys
from dataclasses import dataclass
from collections import OrderedDict

import jinja2
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generates source files based on a jinja2 template "
                    "and a json variable map")
    parser.add_argument(
        '-t', '--template', required=True,
        help='path to the jinja2 template dir')
    parser.add_argument(
        '-m', '--map', required=True,
        help='path to the json variable map file')
    parser.add_argument(
        '-o', '--output', required=True,
        help='path to the output dir')
    parser.add_argument(
        '--title', default="C++ API Reference",
        help='The title of the index for the API'
    )

    return parser.parse_args()


scope_re_cache = dict()


def create_jinja_env(path) -> jinja2.Environment:
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(path),
                             keep_trailing_newline=True, trim_blocks=True, lstrip_blocks=True,
                             extensions=["jinja2.ext.debug"])
    return env


def read_var_map(path):
    with open(path, "r") as f:
        return json.loads(f.read())


def strip_class_name_specialization(name):
    return ''.join(name.partition('<')[0:1]).rstrip()


def is_class_name_specialization(name):
    return strip_class_name_specialization(name) != name


@dataclass
class Context(object):
    class_names: dict
    scope: str | None = None
    raw: bool = False


def stringify(expr, ctx: Context = Context({})):
    raw_ctx = dc.replace(ctx, raw=True)

    def remove_matching_braces(s: str) -> str:
        if len(s) == 0:
            return str()
        if s[0] != "<":
            return s
        nesting_level = -1
        for i, c in enumerate(s):
            match (c, nesting_level):
                case (">", 0):
                    return s[i + 1:]
                case (">", _):
                    nesting_level = nesting_level - 1
                case ("<", _):
                    nesting_level = nesting_level + 1
        raise RuntimeError(f"Encountered unbalanced template brackets in string: {s}")

    def normalize(s: str, scope: str | None):
        if scope is None:
            return s
        prefix = f"{scope}"
        idx = 0
        while 0 <= idx < len(s):
            idx = s.find(prefix, idx)
            if idx >= 0:
                r = remove_matching_braces(s[idx + len(prefix):])
                if len(r) >= 2 and r[:2] == "::":
                    s = s[:idx] + r[2:]
                else:
                    idx = -1
        return s

    def force_single_line(para):
        try:
            if len(para) > 1:
                raise
            return normalize("".join(para[0]).rstrip(), ctx.scope)
        except:
            print(f"Encountered nested paragraphs: {para}", file=sys.stderr)
            return ""
            # raise RuntimeError("Can't handle parameter description with multiple paragraphs")

    match expr:
        case str(body):
            return body
        case list(l):
            return [stringify(elems, ctx) for elems in l]
        case {"@id": id, **kwargs}:
            return stringify({"id": id, **kwargs}, ctx)
        case {"@refid": id, "#text": label}:
            if ctx.raw:
                return label
            else:
                bracket_replacement = '\\<'
                id_str = f"<{id}>" if id else ""
                return f":std:ref:`{label.replace('<', bracket_replacement)}{id_str}`"
        case {"@refid": id, "scope": {"#text": label_scope}, "name": name}:
            label = "::".join((label_scope, name)) if label_scope else name
            return stringify({"@refid": id, "#text": label})
        case {"ref": ref}:
            return stringify(ref, ctx)
        case {"formula": {"#text": code}}:
            if code.startswith("\["):
                if not code.endswith("\]"):
                    raise RuntimeError(f"Can't handle math element: {code}")
                code = code.strip("\[]")
                if not isinstance(code, list):
                    code = [code]
                return {"@directive": "math", "lines": [code]}
            else:
                code = code.strip("$")
                return f":math:`{code}`"
        case {"computeroutput": {"#text": code}}:
            return f":code:`{code}`"
        case {"codeline": code}:
            return stringify(code, raw_ctx)
        case {"programlisting": {"style": style, **para}}:
            return {"@directive": "code-block", "@opts": style, "lines": stringify(para, raw_ctx)}
        case {"simplesect": {"@kind": "see", **para}}:
            return f"see {force_single_line(stringify(para))}"
        case {"simplesect": {"@kind": "return", **para}}:
            return f":return: {force_single_line(stringify(para))}"
        case {"simplesect": {"@kind": "note", **para}}:
            return {"@directive": "note", "lines": stringify(para, ctx)}
        case {"simplesect": {"@kind": "warning", **para}}:
            return {"@directive": "warning", "lines": stringify(para, ctx)}
        case {"itemizedlist": {"listitem": items}}:
            return ["\n"] + [f"* {force_single_line(stringify(item['para']))}" for item in items] + ["\n"]
        case {"orderedlist": {"listitem": items}}:
            return ["\n"] + [f"{n}. {force_single_line(stringify(item['para']))}" for n, item in enumerate(items)] + ["\n"]
        case {"blockquote": para}:
            return {"@directive": "epigraph", "lines": stringify(para)}
        case {"type": t, **kwargs}:
            return {"type": stringify(t, raw_ctx), **stringify(kwargs, raw_ctx)}
        case {"parameternamelist": {"parametername": name}, "parameterdescription": desc}:
            desc = force_single_line(stringify(desc))
            return {"name": stringify(name, raw_ctx), "desc": desc}
        case {"parameterlist": {"parameteritem": items, **kwargs}}:
            role = "tparam" if kwargs.get("@kind", "") == "templateparam" else "param"
            items = stringify(items, ctx)
            return [{"@role": f"{role} {item['name']}", "lines": item["desc"]} for item in items]
        case {"@kind": "typedef", "definition": text, **kwargs}:
            def_text = stringify(text, raw_ctx)
            if "using " in def_text:
                def_text = def_text.replace("typedef ", "")
            return {"@kind": "typedef", "definition": def_text, **stringify(kwargs, raw_ctx)}
        case {"para": para}:
            paragraphs = []
            for p in para:
                def flatten(xs):
                    result = []
                    for x in xs:
                        if isinstance(x, list):
                            result += flatten(x)
                        else:
                            result.append(x)
                    return result

                paragraphs.append(flatten(stringify(p, ctx)))
            return paragraphs
        case {"ulink": {"@url": url, "#text": text}}:
            return f"`{text} <{url}>`_"
        case {"heading": {"@level": level, **text}}:
            level = int(level)
            text = stringify(text, ctx)
            sym = {0: "#", 1: "*", 2: "=", 3: "-", 4: "^", 5: '"'}
            return f'{sym[level] * len(text)}\n{text}\n{sym[level] * len(text)}'
        case {"bold": text}:
            return f"**{stringify(text, ctx)}**"
        case {"emphasis": text}:
            return f"*{stringify(text, ctx)}*"
        case {"ndash": _}:
            return "---"
        case {"#text": text}:
            return normalize(text, ctx.scope)
        case {"inherited": parents, **kwargs}:
            data = {
                **stringify(kwargs, ctx),
                "inherited": {
                    pid: stringify(v, dc.replace(ctx, scope=ctx.class_names[pid])) for pid, v in parents.items()
                }
            }
            return data
        case dict(d):
            return dict(
                (key, stringify(value, ctx)) for key, value in d.items()
            )


def get_class_id_by_name(name, classes):
    for key, data in classes.items():
        if data['name'] == name:
            return key
        # endif
    # endfor
    print("Couldn't find name in class")
    exit(-1)


def extract_class_template_parameters(data: dict) -> dict:
    """Extract template parameters description form brief/detailed description

    Since our .rst template introduces sections, we have to make sure that
    the class template parameter description is before any sections within
    a class. Thus, the description is removed from the normal doxygen place,
    and put into its own array.
    """
    template_desc = []
    for desc in ["briefdescription", "detaileddescription"]:
        removal_idxs = []
        for pid, para in enumerate(data[desc]):
            for lid, line in enumerate(para):
                match line:
                    case {"@role": role}:
                        if role.startswith("tparam"):
                            removal_idxs.append((pid, lid))
                    case _:
                        pass
        for pid, lid in removal_idxs:
            template_desc.append(data[desc][pid][lid])
        for pid, lid in sorted(removal_idxs, reverse=True):
            del data[desc][pid][lid]
    return data | {"templatedescription": template_desc}


def main():
    args = parse_args()

    template_dir = Path(args.template)
    template_env = create_jinja_env(template_dir)
    var_map = read_var_map(args.map)

    var_map['title'] = args.title

    all_inner_classes = set()

    for key, data in var_map["classes"].items():
        for ic in data["innerclass"]:
            var_map["classes"][ic] |= {"is_inner": True}
            all_inner_classes.add(ic)

    for key, data in var_map["classes"].items():
        data["specializations"] = {}
        data['is_special'] = is_class_name_specialization(data["name"]) and data["@id"] not in all_inner_classes
        if data['is_special']:
            stripped_name = strip_class_name_specialization(data["name"])
            stripped_id = get_class_id_by_name(stripped_name, var_map["classes"])
            data['specialization_of'] = stripped_id

    for key, data in var_map["classes"].items():
        for inner_key, inner_data in var_map["classes"].items():
            if inner_data['is_special']:
                if key == inner_data['specialization_of'] and key != inner_data['name']:
                    data['specializations'][inner_key] = {'name': inner_data['name']}

    class_names = {id: c["name"] for id, c in var_map["classes"].items()}

    MAX_NUM_CLASSES = 20
    random.seed(138)
    # var_map["classes"] = {k: v for k, v in random.sample(list(var_map["classes"].items()),
    #                                                      min(len(var_map["classes"]), MAX_NUM_CLASSES))}

    out_dir = Path(args.output)

    class_template = template_env.get_template("class.rst.jinja")
    for key, data in var_map["classes"].items():
        # This is safer for use with http urls
        class_id = key
        out_name = class_id + ".rst"
        out_file = out_dir / out_name
        data["specializations"] = dict(sorted(data["specializations"].items(), key=lambda k: k[1]["name"]))
        data["hidden"] = data.get("is_special", False) or data.get("is_inner", False)
        ctx = Context(class_names, data["name"])
        with open(out_file, "w") as f:
            string_data = stringify(data, ctx=ctx)
            string_data = extract_class_template_parameters(string_data)
            string_data.update(class_names=class_names)
            f.write(class_template.render(string_data))
        # endwith
    # endfor

    allowed_namespaces = ["gko"]

    namespace_template = template_env.get_template("namespace.rst.jinja")
    for key, data in var_map["namespaces"].items():
        # This is safer for use with http urls
        name = data["name"]
        namespace_id = key
        out_name = namespace_id + ".rst"
        out_file = out_dir / out_name
        data["hidden"] = not (any((ns in name for ns in allowed_namespaces)) and any(len(m) for m in data["sectiondef"].values()))
        for sec, members in data["sectiondef"].items():
            members = OrderedDict(sorted(members.items(), key=lambda t: t[1]["name"]))
            data["sectiondef"][sec] = members
        ctx = Context({}, name)
        with open(out_file, "w") as f:
            string_data = stringify(data, ctx=ctx)
            f.write(namespace_template.render(string_data))


    # out_globs = out_dir / "globals.rst"
    # template_globs = read_template(template_dir / "globals.rst.tmpl")
    # with open(out_globs, "w") as f:
    #     f.write(template_globs.render(var_map))
    # endwith

    out_index = out_dir / "index.rst"
    index_template = template_env.get_template("index.rst.jinja")
    var_map["classes"] = dict(sorted(var_map["classes"].items(), key=lambda k: k[1]['name']))
    with open(out_index, "w") as f:
        f.write(index_template.render(var_map))


if __name__ == "__main__":
    main()
