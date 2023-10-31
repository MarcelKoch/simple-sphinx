#!/usr/bin/env python3
import argparse
import json
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
        return jinja2.Template(f.read(), keep_trailing_newline=True, trim_blocks=True)


def read_var_map(path):
    with open(path, "r") as f:
        return json.loads(f.read())
    # endwith

def strip_class_name_specialization(name):
    return ''.join(name.partition('<')[0:1]).rstrip();

def is_class_name_specialization(name):
    return strip_class_name_specialization(name) != name;

def stringify(expr):
    match expr:
        case str(body):
            return body
        case list(l):
            return [stringify(elems) for elems in l]
        case {"type": "reference", "name": name}:
            return f":any:`{name}`"
        case {"type": "inline_math", "code": code}:
            return f":math:`{code}`"
        case {"type": "inline_code", "code": code}:
            return f":code:`{code}`"
        case {"type": "block_code", "code": code, "style": style}:
            return {"type": "block_code", "style": style, "code": code.splitlines()}
        case {"type": "parameter", "name": name, "description": desc}:
            return f":param {name}: {desc}"
        case dict(d):
            return dict(
                (key, stringify(value)) for key, value in d.items()
            )

def get_class_id_by_name(name, classes):
    for key, data in classes.items():
        if data['name'] == name:
            return key;
        #endif
    #endfor
    print("Couldn't find name in class");
    exit(-1);

def main():
    args = parse_args();

    template_dir = Path(args.template);
    template = read_template(template_dir / "class.rst.tmpl");
    var_map = read_var_map(args.map);

    var_map['title'] = args.title;

    for key, data in var_map["classes"].items():
        data["specializations"] = {};
        data['is_special'] = is_class_name_specialization(data["name"]);
        if data['is_special']:
            stripped_name = strip_class_name_specialization(data["name"]);
            stripped_id = get_class_id_by_name(stripped_name, var_map["classes"]);
            data['specialization_of'] = stripped_id;
        #endif
    #endfor
    for key, data in var_map["classes"].items():
        for inner_key, inner_data in var_map["classes"].items():
            if inner_data['is_special']:
                if key == inner_data['specialization_of'] and key != inner_data['name']:
                    data['specializations'][inner_key] = {'name':inner_data['name']};
            #endif
        #endfor
    #endfor

    out_dir = Path(args.output)
    for key, data in var_map["classes"].items():
        # This is safer for use with http urls
        class_name = key
        out_name = class_name + ".rst"
        out_file = out_dir / out_name
        data["specializations"] = dict(sorted(data["specializations"].items(), key=lambda k:k[1]["name"]))
        with open(out_file, "w") as f:
            f.write(template.render(stringify(data)))
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
    var_map["classes"] = dict(sorted(var_map["classes"].items(), key = lambda k: k[1]['name']));
    with open(out_index, "w") as f:
        f.write(template_index.render(var_map))


if __name__ == "__main__":
    main()
