#!/usr/bin/env python3
import argparse
import json
import sys
from itertools import groupby

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


def read_template(path):
    with open(path, "r") as f:
        return jinja2.Template(f.read(), keep_trailing_newline=True, trim_blocks=True, lstrip_blocks=True)

def read_var_map(path):
    with open(path, "r") as f:
        return json.loads(f.read())
    # endwith


def strip_class_name_specialization(name):
    return ''.join(name.partition('<')[0:1]).rstrip()


def is_class_name_specialization(name):
    return strip_class_name_specialization(name) != name


def stringify(expr):
    def force_single_line(para):
        try:
            if len(para) > 1:
                raise
            return "".join(para[0]).rstrip()
        except:
            print(f"Encountered nested paragraphs: {para}", file=sys.stderr)
            return ""
            # raise RuntimeError("Can't handle parameter description with multiple paragraphs")

    match expr:
        case str(body):
            return body
        case list(l):
            return [stringify(elems) for elems in l]
        case {"@id": id, **kwargs}:
            return stringify({"id": id, **kwargs})
        case {"@refid": id, "#text": name}:
            bracket_replacement = '\\<'
            id_str = f"<{id}>" if id else ""
            return f":any:`{name.replace('<', bracket_replacement)}{id_str}`"
        case {"ref": ref}:
            return stringify(ref)
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
            return stringify(code)
        case {"programlisting": {"style": style, **para}}:
            return {"@directive": "code-block", "@opts": style, "lines": stringify(para)}
        case {"@kind": "parameter", "name": name, "description": desc}:
            return f":param {name}: {desc}"
        case {"@kind": "templateparameter", "parameter": param}:
            return ' '.join(stringify(param))
        case {"simplesect": {"@kind": "see", **para}}:
            return f"see {force_single_line(stringify(para))}"
        case {"simplesect": {"@kind": "return", **para}}:
            return f":return: {force_single_line(stringify(para))}"
        case {"simplesect": {"@kind": "note", **para}}:
            return {"@directive": "note", "lines": stringify(para)}
        case {"simplesect": {"@kind": "warning", **para}}:
            return {"@directive": "warning", "lines": stringify(para)}
        case {"itemizedlist": {"listitem": items}}:
            return ["\n"] + [f"* {force_single_line(stringify(item['para']))}" for item in items] + ["\n"]
        case {"orderedlist": {"listitem": items}}:
            return ["\n"] + [f"{n}. {force_single_line(stringify(item['para']))}" for n, item in enumerate(items)] + ["\n"]
        case {"blockquote": para}:
            return {"@directive": "epigraph", "lines": stringify(para)}
        case {"@kind": kind, "parametername": name, "parameterdescription": desc}:
            role = "tparam" if kind == "templateparameter" else "param"
            return {"@role": f"{role} {name}", "lines": stringify({'para': desc})}
        case {"parameternamelist": {"parametername": name}, "parameterdescription": desc}:
            desc = force_single_line(stringify(desc))
            return {"name": stringify(name), "desc": desc}
        case {"parameterlist": {"parameteritem": items, **kwargs}}:
            role = "tparam" if kwargs.get("@kind", "") == "templateparam" else "param"
            items = stringify(items)
            return [{"@role": f"{role} {item['name']}", "lines": item["desc"]} for item in items]
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
                paragraphs.append(flatten(stringify(p)) + ["\n"])
            return paragraphs
        case {"ulink": {"@url": url, "#text": text}}:
            return f"`{text} <{url}>`_"
        case {"heading": {"@level": level, "#text": text}}:
            level = int(level)
            sym = {0: "#", 1: "*", 2: "=", 3: "-", 4: "^", 5: '"'}
            return f'{sym[level] * len(text)}\n{text}\n{sym[level] * len(text)}'
        case {"bold": text}:
            return f"**{stringify(text)}**"
        case {"emphasis": text}:
            return f"*{stringify(text)}*"
        case {"ndash": _}:
            return "---"
        case {"#text": text}:
            return text
        case dict(d):
            return dict(
                (key, stringify(value)) for key, value in d.items()
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
    template = read_template(template_dir / "class.rst.tmpl")
    var_map = read_var_map(args.map)

    var_map['title'] = args.title

    for key, data in var_map["classes"].items():
        data["specializations"] = {}
        data['is_special'] = is_class_name_specialization(data["name"])
        if data['is_special']:
            stripped_name = strip_class_name_specialization(data["name"])
            stripped_id = get_class_id_by_name(stripped_name, var_map["classes"])
            data['specialization_of'] = stripped_id

    for key, data in var_map["classes"].items():
        for inner_key, inner_data in var_map["classes"].items():
            if inner_data['is_special']:
                if key == inner_data['specialization_of'] and key != inner_data['name']:
                    data['specializations'][inner_key] = {'name': inner_data['name']}

    for key, data in var_map["classes"].items():
        for ic in data["innerclass"]:
            var_map["classes"][ic] |= {"is_inner": True}

    out_dir = Path(args.output)
    for key, data in var_map["classes"].items():
        # This is safer for use with http urls
        class_name = key
        out_name = class_name + ".rst"
        out_file = out_dir / out_name
        data["specializations"] = dict(sorted(data["specializations"].items(), key=lambda k: k[1]["name"]))
        data["hidden"] = data.get("is_special", False) or data.get("is_inner", False)
        with open(out_file, "w") as f:
            string_data = stringify(data)
            string_data = extract_class_template_parameters(string_data)
            f.write(template.render(string_data))
        # endwith
    # endfor

    # out_globs = out_dir / "globals.rst"
    # template_globs = read_template(template_dir / "globals.rst.tmpl")
    # with open(out_globs, "w") as f:
    #     f.write(template_globs.render(var_map))
    # endwith

    out_index = out_dir / "index.rst"
    template_index = read_template(template_dir / "index.rst.tmpl")
    # print(json.dumps(stringify(var_map), indent=2))
    var_map["classes"] = dict(sorted(var_map["classes"].items(), key=lambda k: k[1]['name']))
    with open(out_index, "w") as f:
        f.write(template_index.render(var_map))


if __name__ == "__main__":
    main()
