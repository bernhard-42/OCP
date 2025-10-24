#!/usr/bin/env python3
"""
Dump parsed_output.pkl to a readable YAML format for comparison across OSes.

This script extracts ModuleInfo objects from the pickle file and creates a
normalized, sorted representation that can be compared across different platforms.
"""

import pickle
import sys
from pathlib import Path
from collections import OrderedDict
import yaml


def serialize_function(func):
    """Serialize FunctionInfo to a comparable dict."""
    return {
        'name': func.name,
        'return_type': func.return_type,
        'args': [(name, typ) for name, typ, _ in func.args],  # Exclude default values
        'inline': func.inline,
        'namespace': func.namespace,
    }


def serialize_method(method):
    """Serialize MethodInfo to a comparable dict."""
    return {
        'name': method.name,
        'return_type': method.return_type,
        'args': [(name, typ) for name, typ, _ in method.args],  # Exclude default values
        'const': method.const,
        'virtual': method.virtual,
        'pure_virtual': method.pure_virtual,
        'inline': method.inline,
    }


def serialize_field(field):
    """Serialize FieldInfo to a comparable dict."""
    return {
        'name': field.name,
        'type': field.type,
        'const': field.const,
        'pod': field.pod,
    }


def serialize_enum(enum):
    """Serialize EnumInfo to a comparable dict."""
    return {
        'name': enum.name,
        'values': enum.values,
        'anonymous': enum.anonymous,
    }


def serialize_typedef(typedef):
    """Serialize TypedefInfo to a comparable dict."""
    result = {
        'name': typedef.name,
        'type': typedef.type,
        'pod': typedef.pod,
    }
    if hasattr(typedef, 'template_base') and typedef.template_base:
        result['template_base'] = typedef.template_base
    if hasattr(typedef, 'template_args') and typedef.template_args:
        result['template_args'] = typedef.template_args
    return result


def serialize_class(cls):
    """Serialize ClassInfo to a comparable dict."""
    result = OrderedDict([
        ('name', cls.name),
        ('abstract', cls.abstract),
        ('superclass', sorted(cls.superclass)),
        ('counts', OrderedDict([
            ('constructors', len(cls.constructors)),
            ('methods', len(cls.methods)),
            ('static_methods', len(cls.static_methods)),
            ('operators', len(cls.operators)),
            ('fields', len(cls.fields)),
            ('enums', len(cls.enums)),
        ])),
    ])

    # Add detailed info for non-empty collections
    if cls.fields:
        result['fields'] = [serialize_field(f) for f in sorted(cls.fields, key=lambda x: x.name)]

    if cls.enums:
        result['enums'] = [serialize_enum(e) for e in sorted(cls.enums, key=lambda x: x.name)]

    # Add constructor signatures (name is always the class name, so just count args)
    if cls.constructors:
        result['constructor_signatures'] = sorted([
            {'arg_types': [typ for _, typ, _ in c.args]}
            for c in cls.constructors
        ], key=lambda x: str(x))

    # Add method names (detailed signatures omitted for brevity)
    if cls.methods:
        result['method_names'] = sorted([m.name for m in cls.methods])

    if cls.static_methods:
        result['static_method_names'] = sorted([m.name for m in cls.static_methods])

    if cls.operators:
        result['operator_names'] = sorted([m.name for m in cls.operators])

    return result


def serialize_class_template(cls_tmpl):
    """Serialize ClassTemplateInfo to a comparable dict."""
    result = serialize_class(cls_tmpl)
    result['type_params'] = [
        {
            'type': typ,
            'name': name,
            'default': default,
        }
        for typ, name, default in cls_tmpl.type_params
    ]
    return result


def serialize_module(module):
    """Serialize ModuleInfo to a comparable dict."""
    result = OrderedDict([
        ('name', module.name),
        ('dependencies', sorted(module.dependencies_headers)),
        ('namespaces', sorted(module.namespaces)),
        ('counts', OrderedDict([
            ('headers', len(module.headers)),
            ('classes', len(module.classes)),
            ('class_templates', len(module.class_templates)),
            ('typedefs', len(module.typedefs)),
            ('enums', len(module.enums)),
            ('functions', len(module.functions)),
            ('operators', len(module.operators)),
        ])),
    ])

    # Add classes (sorted by name)
    if module.classes:
        result['classes'] = OrderedDict([
            (cls.name, serialize_class(cls))
            for cls in sorted(module.classes, key=lambda x: x.name)
        ])

    # Add class templates
    if module.class_templates:
        result['class_templates'] = OrderedDict([
            (tmpl.name, serialize_class_template(tmpl))
            for tmpl in sorted(module.class_templates, key=lambda x: x.name)
        ])

    # Add typedefs
    if module.typedefs:
        result['typedefs'] = [
            serialize_typedef(t)
            for t in sorted(module.typedefs, key=lambda x: x.name)
        ]

    # Add enums
    if module.enums:
        result['enums'] = [
            serialize_enum(e)
            for e in sorted(module.enums, key=lambda x: x.name)
        ]

    # Add functions (just names and arg counts for brevity)
    if module.functions:
        result['function_names'] = sorted([
            {'name': f.name, 'arg_count': len(f.args)}
            for f in module.functions
        ], key=lambda x: (x['name'], x['arg_count']))

    if module.operators:
        result['operator_names'] = sorted([
            {'name': f.name, 'arg_count': len(f.args)}
            for f in module.operators
        ], key=lambda x: (x['name'], x['arg_count']))

    return result


def dump_parsed_pkl(pkl_path, output_path):
    """Load pickle file and dump to YAML."""
    print(f"Loading {pkl_path}...")

    with open(pkl_path, 'rb') as f:
        modules = pickle.load(f)

    print(f"Found {len(modules)} modules")

    # Create summary
    summary = OrderedDict([
        ('total_modules', len(modules)),
        ('total_classes', sum(len(m.classes) for m in modules)),
        ('total_class_templates', sum(len(m.class_templates) for m in modules)),
        ('total_typedefs', sum(len(m.typedefs) for m in modules)),
        ('total_enums', sum(len(m.enums) for m in modules)),
        ('total_functions', sum(len(m.functions) for m in modules)),
    ])

    # Serialize all modules
    print("Serializing modules...")
    serialized_modules = OrderedDict([
        (module.name, serialize_module(module))
        for module in sorted(modules, key=lambda x: x.name)
    ])

    # Create output structure
    output = OrderedDict([
        ('summary', summary),
        ('modules', serialized_modules),
    ])

    # Write to YAML
    print(f"Writing to {output_path}...")
    with open(output_path, 'w') as f:
        yaml.dump(
            output,
            f,
            default_flow_style=False,
            sort_keys=False,
            width=120,
            indent=2,
        )

    print("Done!")
    print(f"\nSummary:")
    print(f"  Modules: {summary['total_modules']}")
    print(f"  Classes: {summary['total_classes']}")
    print(f"  Class Templates: {summary['total_class_templates']}")
    print(f"  Typedefs: {summary['total_typedefs']}")
    print(f"  Enums: {summary['total_enums']}")
    print(f"  Functions: {summary['total_functions']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python dump_parsed.py <parsed_output.pkl> [output.yml]")
        print("\nExample:")
        print("  python dump_parsed.py parsed_output.pkl parsed_dump.yml")
        sys.exit(1)

    pkl_path = Path(sys.argv[1])
    if not pkl_path.exists():
        print(f"Error: File not found: {pkl_path}")
        sys.exit(1)

    # Default output path
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    else:
        output_path = pkl_path.with_name('parsed_dump.yml')

    dump_parsed_pkl(pkl_path, output_path)


if __name__ == '__main__':
    main()
