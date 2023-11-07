from collections import defaultdict

import sys
import argparse
from dataclasses import dataclass
from functools import singledispatch, reduce
import xml.dom.minidom as MD
from pathlib import Path
import json
from frozendict import frozendict
import xmltodict

gko_directory = "../../ginkgo/document-create-functions/doc/doxygen/xml"
simple_directory = "doxygen/xml"


def dispatch_index(path: Path):
    data = dict(
        classes=dict(),
        namespaces=dict(),
        globals=dict(sectiondef=dict())
    )

    ignored_nodes = {
        "inheritancegraph",
        "collaborationgraph",
        "inbodydescription"
    }

    cdata_sep = '§§'

    def as_list(v):
        if isinstance(v, list):
            return v
        else:
            return [v]

    def post_process(_, key, value):
        if key in ignored_nodes:
            return key, None
        if value is None:
            return key, None
        if isinstance(value, str) and value.strip() == "":
            return key, None
        # transformation based on value
        if isinstance(value, dict):
            if "sectiondef" in value:
                sections = value["sectiondef"]
                value["sectiondef"] = reduce(lambda r, s: r | {s["@kind"]: s["memberdef"]}, sections, dict())
            if "memberdef" in value:
                members = value["memberdef"]
                value["memberdef"] = reduce(lambda r, s: r | {s["@id"]: s}, members, dict())
            if "innerclass" in value:
                innerclasses = value["innerclass"]
                value["innerclass"] = [ic["@refid"] for ic in innerclasses]
            if "innernamespace" in value:
                innernamespace = value["innernamespace"]
                value["innernamespace"] = [ic["@refid"] for ic in innernamespace]
            if len(value) == 1 and "#text" in value:
                value = value["#text"]
        # transformation based on key
        if key == "ref":
            return key, {"@kind": key, **value}
        if key == "formula":
            code = value["#text"]
            if code.startswith("\\[") and code.endswith("\\]"):
                return key, {'@kind': 'block_math', "@id": value["@id"], 'code': code.strip("\[] ")}
            elif code.startswith("$") and code.endswith("$"):
                return key, {'@kind': 'inline_math', "@id": value["@id"], 'code': code.strip("$ ")}
            else:
                raise AssertionError(f"Unrecognized math formula: {code}")
        if key == "computeroutput":
            return key, {"@kind": 'inline_code', "code": value}
        if key == "codeline":
            return key, " ".join([(cl or "").strip() for cl in as_list(value["highlight"])])
        if key == "highlight":
            if "#text" not in value:
                return key, None
            return key, value["#text"].replace(cdata_sep, " ")
        if key == "programlisting":
            style = "text"
            codeline = value["codeline"]
            if "@filename" in value:
                style = value["@filename"][1:] + codeline[0]
                codeline = codeline[1:]
            return key, {"@style": style, "codeline": codeline}
        if key in ["detaileddescription", "briefdescription"]:
            return key, value or []
        if key == "para":
            if not isinstance(value, dict):
                value = {'#text': value}

            texts = (value.get('#text', "") or "").split(cdata_sep)

            other_keys = set(value.keys()) - {'#text'}
            other_keys = set(k for k in other_keys if value[k])
            interleaved = sum([as_list(value[k]) for k in other_keys], [])

            if len(interleaved) == len(texts) - 1:
                value = sum(([{'#text': t}, il] for t, il in zip(texts, interleaved)), []) + [{'#text': texts[-1]}]
            elif len(interleaved) == len(texts) + 1:
                value = [interleaved[0]] + sum(([{'#text': t}, il] for t, il in zip(texts, interleaved[1:])), [])
            elif texts == [""]:
                value = interleaved
            else:
                # print(f"Non matching number of interleaved segments found in para: {value}, will put text "
                #       f"segments before interleaved segments", file=sys.stderr)
                value = sum(([{'#text': t}, il] for t, il in zip(texts, interleaved)), [])
            return key, value
        if key in ["parameteritem", "memberdef",
                   "detaileddescription", "briefdescription", "listofallmembers", "param",
                   "templateparamlist"]:
            if isinstance(value, dict) and "#text" in value:
                del value["#text"]
            return key, value
        if key in ["parameternamelist", "parameterdescription"]:
            del value["#text"]
            value = {list(value.keys())[0]: list(value.values())[0]}
            return key, value
        if key == "compounddef":
            del value["#text"]
            if value["@kind"] == "file":
                del value["programlisting"]
            if value["@kind"] in ["class", "struct", "union"]:
                value.setdefault("innerclass", [])
                value.setdefault("briefdescription", [])
                value.setdefault("detaileddescription", [])
                value["name"] = value["compoundname"]
                del value["compoundname"]
        return key, value

    with open(path / "index.xml") as input:
        index = xmltodict.parse(input.read())["doxygenindex"]

    map_scope = {"class": "classes", "struct": "classes", "union": "classes",
                "namespace": "namespaces", "file": "globals"}
    for compound in index["compound"]:
        try:
            scope = map_scope[compound['@kind']]
        except KeyError:
            continue

        with open(path / f"{compound['@refid']}.xml") as input:
            new_data = xmltodict.parse(input.read(), postprocessor=post_process,
                                       force_list=["sectiondef", "memberdef", "innerclass", "innernamespace", "param",
                                                   "templateparameterlist", "parameterlist", "derivedcompoundref",
                                                   "basecompoundref",
                                                   "para"], strip_whitespace=False,
                                       force_cdata=True,
                                       cdata_separator=cdata_sep)["doxygen"]
            new_data = new_data["compounddef"]
        if scope == "classes":
            data[scope][new_data["@id"]] = new_data
        if scope == "namespaces":
            data[scope][new_data["@id"]] = new_data
        if scope == "globals":
            innerclasses = new_data.pop('innerclass', [])
            innernamespaces = new_data.pop('innernamespace', [])
            sections = new_data.pop('sectiondef', dict())
            stripped_sections = defaultdict(list)
            for sec_type, members in sections.items():
                for member in members.values():
                    stripped_sections[sec_type].append({
                        '@refid': member['@id'],
                        '@prot': member['@prot'],
                        'name': member['name']
                    })

            data[scope][new_data["@id"]] = {**new_data, 'contains': {
                'classes': innerclasses,
                'namespaces': innernamespaces,
                **stripped_sections
            }}

            for sec_type, members in sections.items():
                for member_id, member in members.items():
                    data[scope]['sectiondef'].setdefault(sec_type, dict())[member_id] = member

    return data


xml_directory = simple_directory

parser = argparse.ArgumentParser(
    description="Translates doxygen xml output into a more sensible format"
)

parser.add_argument('-d', '--doxygen',
                    required=False,
                    default=xml_directory,
                    help="Path to the doxygen generated xml directory"
                    )

args = parser.parse_args()

xml_directory = Path(args.doxygen or xml_directory)

parsed = dispatch_index(xml_directory)

print(json.dumps(parsed, indent=2))


def compute_extra_data(data):
    specializations = defaultdict(set)
    specialization_of = defaultdict(dict)
    enclosing_class = defaultdict(lambda: None)
    name_to_id = defaultdict(set)

    def build_name_to_id(_data):
        match _data:
            case {"id": id, "name": name, **kwargs}:
                name_to_id[name].add(id)
                build_name_to_id(kwargs)
            case list(l):
                for v in l:
                    build_name_to_id(v)
            case dict(kwargs):
                for v in kwargs.values():
                    build_name_to_id(v)
            case _:
                pass

    build_name_to_id(data)

    def remove_specialization(name):
        return name.partition('<')[0]

    def maybe_add_specialization(cl_id, cl):
        name = cl["name"]
        trimmed_name = remove_specialization(name)
        if name != trimmed_name and trimmed_name in name_to_id:
            specializations[name_to_id[trimmed_name]].add(cl_id)
            specialization_of[name_to_id[name]], _ = name_to_id[trimmed_name]

    for cl_id, cl in data['classes'].items():
        maybe_add_specialization(cl_id, cl)

    for ic in cl["innerclass"]:
        enclosing_class[ic["refid"]] = cl_id

    return name_to_id, specializations, specialization_of, enclosing_class


# ctx = compute_extra_data(parsed)
pass
