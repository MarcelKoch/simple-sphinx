from collections import defaultdict

import argparse
from dataclasses import dataclass
from enum import Enum, auto
from functools import singledispatch, reduce
import xml.dom.minidom as MD
from pathlib import Path
import json
from typing import Any

gko_directory = "../../ginkgo/document-create-functions/doc/doxygen/xml"
simple_directory = "doxygen/xml"

enum_types = set()


class UniqueEnumType(Enum):
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> Any:
        new_type = type(name, (object,), dict())
        enum_types.add(new_type)
        return new_type


class xml_tag(UniqueEnumType):
    """XML tags which have a non-default dispatch

    The tag defined here are one-to-one mappings of the `kind` attribute
    of the xml Element node. The different `kind`s represent different
    doxygen parts. The ones defined here need special treatment.
    """

    COMPOUNDDEF = auto()
    DETAILEDDESCRIPTION = auto()
    BRIEFDESCRIPTION = auto()
    INNERCLASS = auto()
    HIGHLIGHT = auto()
    NAME = auto()
    PARA = auto()
    PARAMETERDESCRIPTION = auto()
    PROGRAMLISTING = auto()
    SECTIONDEF = auto()
    SP = auto()
    TYPE = auto()


NO_TEXT = {
    "compounddef",
    "listofallmembers",
    "memberdef",
    "param",
    "parameteritem",
    "parameterlist",
    "parameternamelist",
    "templateparamlist"
}

FORCE_LIST = {
    "param",
    "parameteritem"
}


def as_list(v):
    if isinstance(v, list):
        return v
    else:
        return [v]


@singledispatch
def dispatch(expr, ctx):
    raise AssertionError(f"Unhandled type {type(expr)}")


@singledispatch
def dispatch_tag(tag, expr, ctx):
    raise AssertionError(f"Unhandled tag {tag}")


@dispatch.register
def dispatch_(expr: MD.Document, ctx):
    return dispatch(expr.getElementsByTagName("doxygen")[0], ctx)


def dispatch_default(expr: MD.Element, ctx):
    def merge(a: dict, b: dict):
        common_keys = set(a.keys()) & set(b.keys())
        unique_kwargs = [(k, a[k]) for k in set(a.keys()) - common_keys] + [(k, b[k]) for k in
                                                                            set(b.keys()) - common_keys]
        shared_kwargs = [(k, as_list(a[k]) + as_list(b[k])) for k in common_keys]
        merged = dict(unique_kwargs + shared_kwargs)
        if "#text" in merged:
            merged["#text"] = "".join(merged["#text"])
        return merged

    tag = expr.tagName
    attribs = {f"@{k}": v for k, v in expr.attributes.items()}
    data = {tag: reduce(lambda r, c: merge(r, dispatch(c, ctx)), expr.childNodes, attribs)}

    if tag in NO_TEXT:
        if "#text" in data[tag]:
            del data[tag]["#text"]
    if tag in FORCE_LIST:
        data = {tag: as_list(data[tag])}

    return data


@dispatch.register
def dispatch_(expr: MD.Element, ctx):
    try:
        tag = xml_tag[expr.tagName.upper()].value()
    except KeyError:
        data = dispatch_default(expr, ctx)
    else:
        data = dispatch_tag(tag, expr, ctx)

    return data


@dispatch.register
def dispatch_(expr: MD.Text, ctx):
    return {"#text": expr.data}


@dispatch_tag.register
def dispatch_tag_(tag: xml_tag.SP.value, expr: MD.Element, ctx):
    return {"#text": " "}


@dispatch_tag.register
def dispatch_tag_(tag: xml_tag.PARA.value, expr: MD.Element, ctx):
    return {"para": [dispatch(c, ctx) for c in expr.childNodes]}


@dispatch_tag.register
def dispatch_tag_(tag: xml_tag.COMPOUNDDEF.value, expr: MD.Element,
                  ctx):
    data = dispatch_default(expr, ctx)[expr.tagName]
    data["name"] = data["compoundname"]["#text"]
    sections = as_list(data.get("sectiondef", [dict()]))
    data["sectiondef"] = reduce(lambda r, d: r | d, sections, dict())
    for key in ["innerclass", "derivedcompoundref", "basecompoundref"]:
        data[key] = as_list(data.get(key, []))
    for key in ["inheritancegraph", "collaborationgraph", "compoundname"]:
        if key in data:
            del data[key]
    return {expr.tagName: data}


@dispatch_tag.register
def dispatch_tag_(tag: xml_tag.SECTIONDEF.value, expr: MD.Element, ctx):
    data = dispatch_default(expr, ctx)
    section_data = defaultdict(dict)
    for sec in as_list(data["sectiondef"]):
        kind = sec["@kind"]
        for member in as_list(sec["memberdef"]):
            section_data[kind][member["@id"]] = member
    return {"sectiondef": section_data}


@dispatch_tag.register
def dispatch_tag_(
        tag: xml_tag.DETAILEDDESCRIPTION.value | xml_tag.BRIEFDESCRIPTION.value | xml_tag.PARAMETERDESCRIPTION.value,
        expr: MD.Element, ctx):
    data = dispatch_default(expr, ctx)
    return {expr.tagName: {"para": data[expr.tagName].get("para", [[]])}}


@dispatch_tag.register
def dispatch_tag_(tag: xml_tag.TYPE.value, expr: MD.Element, ctx):
    if children := expr.childNodes:
        return {"type": dispatch(child, ctx) for child in children}
    else:
        return {"type": {"#text": "void"}}


@dispatch_tag.register
def dispatch_tag_(tag: xml_tag.HIGHLIGHT.value, expr: MD.Element, ctx):
    data = dispatch_default(expr, ctx)
    return {k: v for k, v in data[expr.tagName].items() if k != "@class"}


@dispatch_tag.register
def dispatch_tag_(tag: xml_tag.NAME.value, expr: MD.Element, ctx):
    return {expr.tagName: expr.childNodes[0].data}


@dispatch_tag.register
def dispatch_tag_(tag: xml_tag.INNERCLASS.value, expr: MD.Element, ctx):
    return {expr.tagName: expr.attributes["refid"].value}


@dispatch_tag.register
def dispatch_tag_(tag: xml_tag.PROGRAMLISTING.value, expr: MD.Element, ctx):
    codelines = [dispatch_default(c, ctx) for c in expr.childNodes if
                 isinstance(c, MD.Element) and c.tagName == "codeline"]
    if "filename" in expr.attributes:
        style = expr.attributes["filename"].value.lstrip(".")
    else:
        try:
            first_line = codelines[0]["codeline"]["#text"]
            if first_line.startswith("{") and first_line.endswith("}"):
                codelines = codelines[1:]
                style = first_line.strip("{}")
            else:
                raise
        except:
            style = "text"
    return {expr.tagName: {"style": style, "code": codelines}}


def dispatch_index(expr: MD.Document, ctx):
    data = dict(
        classes=dict(),
        namespaces=dict(),
        globals=dict(sectiondef=dict())
    )

    index = expr.getElementsByTagName('doxygenindex')[0]

    map_kind = {"class": "classes", "struct": "classes", "union": "classes",
                "namespace": "namespaces", "file": "globals"}
    for compoud in index.getElementsByTagName('compound'):
        file = f"{ctx.directory}/{compoud.attributes['refid'].value}.xml"
        kind = compoud.attributes['kind'].value

        try:
            scope = map_kind[kind]
        except KeyError:
            continue

        new_data = dispatch(MD.parse(file), ctx)["doxygen"]["compounddef"]
        if new_data and kind != "file":
            data[scope][new_data["@id"]] = new_data
        if new_data and kind == "file":
            if "programlisting" in new_data:
                del new_data["programlisting"]
            innerclasses = new_data.pop('innerclass', [])
            innernamespaces = new_data.pop('innernamespace', [])
            sections = new_data.pop('sectiondef', dict())
            stripped_sections = defaultdict(list)
            for kind, sec in sections.items():
                for member in sec.values():
                    stripped_sections[kind].append({
                        '@refid': member['@id'],
                        '@prot': member['@prot'],
                        'name': member['name']
                    })

            data[scope][new_data["@id"]] = {**new_data, 'contains': {
                'classes': innerclasses,
                'namespaces': innernamespaces,
                **stripped_sections
            }}

            for kind, sec in sections.items():
                for member in sec.values():
                    data[scope]['sectiondef'].setdefault(kind, dict())[member["@id"]] = member

    return data


@dataclass
class Context(object):
    directory: str


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

xml_directory = args.doxygen or xml_directory

index = Path(xml_directory) / "index.xml"
dom = MD.parse(str(index.resolve()))

parsed = dispatch_index(dom, Context(directory=xml_directory))

print(json.dumps(parsed, indent=2))
