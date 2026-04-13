# OCCT 8.0 Migration Report for OCP

Each section is tagged with the phase of work it belongs to:

- `[7.9-to-8rc3]` — initial 7.9 → 8.0 rc3 migration
- `[8rc3-to-8rc5]` — rc3 → rc5 follow-up

## Table of Contents

### 1 Project & scope

- [1.1 Module list changes](#11-module-list-changes)
- [1.2 Header sync and deleted headers](#12-header-sync-and-deleted-headers)
- [1.3 `OCP_specific.inc` — exception and pybind11 API updates](#13-ocp_specificinc--exception-and-pybind11-api-updates)

### 2 Type recognition

- [2.1 `namespace occ` and handle type recognition](#21-namespace-occ-and-handle-type-recognition)
- [2.2 Native C++ types replace `Standard_*` typedefs](#22-native-c-types-replace-standard_-typedefs)
- [2.3 Missing `std::` prefix on bare std types](#23-missing-std-prefix-on-bare-std-types)

### 3 Template / typedef infrastructure

- [3.1 Register `_H` typedefs as template instantiations](#31-register-_h-typedefs-as-template-instantiations)
- [3.2 Template base class inheritance (HArray1, HArray2, HSequence)](#32-template-base-class-inheritance-harray1-harray2-hsequence)
- [3.3 `NCollection_*::Contained` — pybind11 cast failure](#33-ncollection_contained--pybind11-cast-failure)
- [3.4 `NCollection_*::Bound`, `Seek`, `ChangeSeek` exclusions](#34-ncollection_bound-seek-changeseek-exclusions)
- [3.5 C++ `using` aliases and namespace-scoped class templates](#35-c-using-aliases-and-namespace-scoped-class-templates)
- [3.6 Typedef deduplication via union-find](#36-typedef-deduplication-via-union-find)

### 4 Method / function signatures

- [4.1 `= default` constructors missing](#41--default-constructors-missing)
- [4.2 Unbindable new method signatures](#42-unbindable-new-method-signatures)
- [4.3 Move-assignment `operator=(T&&)` → generic rvalue-reference filter](#43-move-assignment-operatortt--generic-rvalue-reference-filter)
- [4.4 `T* const&` return type doubling](#44-t-const-return-type-doubling)
- [4.5 Copy semantics check](#45-copy-semantics-check)
- [4.6 `noexcept` propagation in trampoline classes](#46-noexcept-propagation-in-trampoline-classes)

### 5 Class structure

- [5.1 Nested enum value clash (`gp_Dir::D`)](#51-nested-enum-value-clash-gp_dird)
- [5.2 Anonymous namespaces exposing internal classes](#52-anonymous-namespaces-exposing-internal-classes)
- [5.3 `Bnd_Box::Limits` nested struct — `references_inner` filter](#53-bnd_boxlimits-nested-struct--references_inner-filter)
- [5.4 `NCollection_` return value policy (segfaults)](#54-ncollection_-return-value-policy-segfaults)
- [5.5 Bare nested type names in generated code](#55-bare-nested-type-names-in-generated-code)
- [5.6 `BRepGraphInc_Populate::Options` registration](#56-brepgraphinc_populateoptions-registration)

### 6 Parse context & exclusions

- [6.1 Namespace-based modules (Math\*, GeomEval, Geom2dEval, GeomBndLib)](#61-namespace-based-modules-math-geomeval-geom2deval-geombndlib)
- [6.2 Forward declaration resolution — DE\* and Geom modules](#62-forward-declaration-resolution--de-and-geom-modules)
- [6.3 OCCT rc5 bugs and unbindable namespace functions](#63-occt-rc5-bugs-and-unbindable-namespace-functions)
- [6.4 New namespace/class exclusions](#64-new-namespaceclass-exclusions)
- [6.5 Parse context fixes for remaining modules](#65-parse-context-fixes-for-remaining-modules)

### 7 Warning suppression

- [7.1 Suppress `#pragma message` warnings (pywrap parse)](#71-suppress-pragma-message-warnings-pywrap-parse)
- [7.2 Suppress compilation warnings](#72-suppress-compilation-warnings)

### 8 macOS Build Environment

- [8.1 RapidJSON CMake variable case](#81-rapidjson-cmake-variable-case)
- [8.2 macOS ARM clang include path handling](#82-macos-arm-clang-include-path-handling)
- [8.3 CMake: `target_compile_options` instead of deprecated `COMPILE_FLAGS`](#83-cmake-target_compile_options-instead-of-deprecated-compile_flags)

---

# 1 Project & scope

## 1.1 Module list changes

`[7.9-to-8rc3]` plus TColgp retention `[8rc3-to-8rc5]`

### 1.1.1 Removed modules

| Module                                                                                                                                                              | Reason                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `Geom2dEvaluator`, `GeomEvaluator`                                                                                                                                  | Replaced by `GeomEval`, `Geom2dEval`, `GeomGridEval` |
| `Geom2dLProp`, `LProp3d`                                                                                                                                            | Removed in OCCT 8.0                                  |
| `NIS`, `Voxel`, `InterfaceGraphic`                                                                                                                                  | Removed in OCCT 8.0                                  |
| `TopClass`                                                                                                                                                          | Headers made private in OCCT 8.0                     |
| `RWStepBasic`, `RWStepGeom`, `RWStepRepr`, `RWStepShape`, `RWStepDimTol`, `RWStepVisual`, `RWStepElement`, `RWStepFEA`, `RWStepAP203`, `RWStepAP214`, `RWStepAP242` | Headers made private (`.pxx`) in OCCT 8.0            |

### 1.1.2 Deprecated but retained modules [8rc3-to-8rc5]

`TColgp`, `TColGeom`, and `TColGeom2d` were initially removed (OCCT 8.0 deprecated the entire modules), but their headers still contain typedef aliases like `TColgp_HArray1OfDir = NCollection_HArray1<gp_Dir>` that pywrap registers as template instantiations. Without these registrations, downstream modules using the types as default argument values fail at import time with "type not registered yet" errors. The `-Wno-deprecated-declarations` flag (section 7.2) suppresses the resulting warnings.

```diff
- #"TColgp",  # removed in OCCT 8.0 (deprecated NCollection aliases)
+ "TColgp",  # deprecated but still needed for HArray1/HArray2/HSequence template registrations
```

Same for `TColGeom` and `TColGeom2d`.

### 1.1.3 New modules (31 total)

**Namespace-based math modules** (new in OCCT 8.0, use C++ namespaces instead of classes): `MathUtils`, `MathRoot`, `MathOpt`, `MathLin`, `MathSys`, `MathInteg`, `MathPoly`

**Geometry evaluation:** `ExtremaPC`, `GeomBndLib`, `GeomEval`, `Geom2dEval`, `Geom2dGridEval`

**Topology graph:** `BRepGraph`, `BRepGraphInc`, `BRepPreviewAPI`, `PointSetLib`

**Presentation/dimensions:** `PrsDim`

**Data exchange:** `StepKinematics`, `DEBREP`, `DESTEP`, `DEIGES`, `DEOBJ`, `DESTL`, `DEPLY`, `DEVRML`, `DEXCAF`

**Other:** `GeomGridEval`, `GeomHash`, `Geom2dHash`, `HelixGeom`, `HelixBRep`, `StepTidy`, `XBRepMesh`

**ocp.toml** — examples of key additions:

```diff
+ "MathUtils", "MathRoot", "MathOpt", "MathLin", "MathSys", "MathInteg", "MathPoly",
+ "ExtremaPC", "GeomBndLib", "GeomEval", "Geom2dEval", "Geom2dGridEval",
+ "BRepGraph", "BRepGraphInc", "BRepPreviewAPI", "PointSetLib",
+ "PrsDim", "StepKinematics",
+ "DEBREP", "DESTEP", "DEIGES", "DEOBJ", "DESTL", "DEPLY", "DEVRML", "DEXCAF",
+ "GeomGridEval", "GeomHash", "Geom2dHash", "HelixGeom", "HelixBRep", "StepTidy",
```

```diff
+ [Modules.XBRepMesh]
+     include_header_pre = """#include <TopoDS_Shape.hxx>
+ #include <BRepMesh_DiscretRoot.hxx>"""
```

---

## 1.2 Header sync and deleted headers

`[7.9-to-8rc3]`

**opencascade/** — synced 6894 `.hxx` files from `/opt/local/occt-master/include/opencascade/`. 300 modified, 33 deleted vs the 7.x baseline. Also copied 1 `.pxx` file (`GeomBndLib_InfiniteHelpers.pxx`) from OCCT source (not installed by cmake install).

| What                                                                                 | Count | Reason                                                                                                                                                                                                                                                                                                                                     |
| ------------------------------------------------------------------------------------ | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Deprecated typedef/iterator headers (e.g. `TColStd_ListIteratorOfListOfInteger.hxx`) | 367   | OCCT 8.0 removed NCollection aliases. These one-line typedef headers no longer exist upstream.                                                                                                                                                                                                                                             |
| Dimension/Relation class headers (e.g. `AIS_Dimension.hxx`, `AIS_Relation.hxx`)      | ~25   | Consolidated into `PrsDim` module in OCCT 8.0.                                                                                                                                                                                                                                                                                             |
| Broken compat headers that `#include` deleted files                                  | 6     | OCCT ships these but never includes them; pywrap picks them up via glob. Deleted: `BOPDS_VectorOfListOfPaveBlock.hxx`, `BOPDS_DataMapOfIntegerListOfPaveBlock.hxx`, `BOPDS_IndexedDataMapOfPaveBlockListOfPaveBlock.hxx`, `BOPDS_DataMapOfPaveBlockListOfPaveBlock.hxx`, `Graphic3d_MapIteratorOfMapOfStructure.hxx`, `TObj_Container.hxx` |
| Removed module headers (Geom2dLProp, LProp3d, etc.)                                  | ~15   | Headers for modules removed in OCCT 8.0 (`.hxx` and `.lxx` files)                                                                                                                                                                                                                                                                          |
| Removed `.lxx` inline files                                                          | ~12   | OCCT 8.0 inlined these into `.hxx` files (e.g. `BRepClass_Edge.lxx`, `Bnd_Sphere.lxx`, `GC_Root.lxx`)                                                                                                                                                                                                                                      |

---

## 1.3 `OCP_specific.inc` — exception and pybind11 API updates

`[7.9-to-8rc3]`

Three breaking changes converge in `OCP_specific.inc`:

1. **`Standard_Failure` no longer inherits from `Standard_Transient`.** Previously OCP could use the transient-handle plumbing to access the exception object. Now it has to use the standard C++ `std::exception` interface (`what()`).
2. **pybind11 2.13 deprecated the direct-call pattern `ex(message)`.** The new API is `py::set_error(ex_class, message)`, which sets the Python exception state properly rather than (incorrectly) constructing a Python object on the C++ stack.
3. **fmt ≥ 9 requires explicit header-only opt-in** when used without linking `libfmt`. OCCT 8.0 bumped its fmt dependency; OCP uses `<fmt/format.h>` through OCCT headers and doesn't link a separate fmt library, so `FMT_HEADER_ONLY` must be defined before the first `<fmt/*>` include.

**OCP_specific.inc**

```diff
  #include <Standard_Handle.hxx>
  #include <type_traits>
  #include <memory>
+ #define FMT_HEADER_ONLY
  #include <fmt/format.h>
```

```diff
  try {
      std::rethrow_exception(p);
  } catch (const CppException &e) {
-     ex(e.GetMessageString());
+     py::set_error(ex, e.what());
  }
```

`e.what()` is `virtual` on `std::exception` and OCCT 8.0's `Standard_Failure::what()` overrides it to return the same string `GetMessageString()` used to return. Behavioral compatibility preserved.

---

# 2 Type recognition

## 2.1 `namespace occ` and handle type recognition

`[7.9-to-8rc3]`

OCCT 8.0 wraps everything in `namespace occ` and replaces the `Handle(T)` macro with `occ::handle<T>`. Both old spellings are kept via backward-compat aliases, so generated code can see any of four forms for the same smart-pointer type:

```cpp
Handle(Geom_Curve)          // legacy macro (still works via alias)
opencascade::handle<Geom_Curve>   // 7.x canonical spelling
handle<Geom_Curve>          // unqualified (inside namespace occ)
occ::handle<Geom_Curve>     // 8.0 canonical spelling
```

libclang's type spelling depends on where the symbol is referenced — inside the `occ` namespace it drops the qualifier; outside it emits the full path. pywrap therefore has to recognize all four.

Two distinct problems follow:

1. **`occ` namespace** must be excluded from binding — otherwise pywrap would try to create a Python submodule `OCP.occ` containing every OCCT class (which is already bound at the top level).
2. **All four handle spellings** must be treated as smart-pointer types so byref-output detection (`handle<T>&`), template-include filtering, and inner-type extraction work.

`GeomGridEval` is also excluded: new in 8.0, internal curve/surface evaluation helpers that shouldn't be bound as a standalone module.

**ocp.toml**

```diff
 exclude_namespaces = [
  "std",
  "opencascade",
  ...
- "Graphic3d_TransformUtils"
+ "Graphic3d_TransformUtils",
+ "GeomGridEval",
+ "occ"
 ]
```

```diff
- byref_types_smart_ptr = ["opencascade::handle", "handle", "Handle"]
+ byref_types_smart_ptr = ["opencascade::handle", "occ::handle", "handle", "Handle"]
```

**pywrap/bindgen/template_sub_pre.j2** — template include block

`td.type.split("_")` on `occ::handle<NCollection_...>` produces a broken `#include "occ::handle<NCollection_tmpl.hxx"`. Add all handle spellings to the exclusion filter.

```diff
 {% if not td.pod and td.template_base.__len__()>0
     and not td.type.startswith("opencascade::handle")
+    and not td.type.startswith("occ::handle")
+    and not td.type.startswith("handle<")
+    and not td.type.startswith("Handle(")
     and not td.type.startswith("std::") %}
```

**pywrap/bindgen/template_sub.j2** — template include block

Same fix as `template_sub_pre.j2`.

```diff
- {% if not td.pod and not "_H" in td.name and td.template_base.__len__()>0
+ {% if not td.pod and td.template_base.__len__()>0
     and not td.type.startswith("opencascade::handle")
+    and not td.type.startswith("occ::handle")
+    and not td.type.startswith("handle<")
+    and not td.type.startswith("Handle(")
     and not td.type.startswith("std::") %}
```

**pywrap/bindgen/\_\_init\_\_.py** — nested template parsing in `type_form_byref_smart_ptr`

The pyparsing expression for extracting the inner type from `handle<T> &` failed on nested templates like `handle<NCollection_Shared<Foo>> &` because `pp.Word(pp.alphanums+'_')` doesn't match `<`, `,`, or spaces.

```diff
  def type_form_byref_smart_ptr(t: str, ptr_types: List[str]) -> str:

+     # Non-greedy match with lookahead to handle nested templates correctly
+     # e.g. handle<NCollection_Shared<Foo>> & -> NCollection_Shared<Foo>
+     inner = pp.Regex(r'[A-Za-z0-9_<>, ]+?(?=>\s*&)')
      expr = (pp.Suppress(pp.Or(map(pp.Literal, ptr_types)) + pp.Literal('<'))
-             + pp.Word(pp.alphanums+'_') + pp.Suppress(pp.Literal('>') + pp.Literal('&')))
+             + inner + pp.Suppress(pp.Regex(r'>\s*&')))

-     return expr.parse_string(t)[0]
+     return expr.parse_string(t)[0].strip()
```

---

## 2.2 Native C++ types replace `Standard_*` typedefs

`[7.9-to-8rc3]`

OCCT 8.0 replaced `Standard_Real`/`Standard_Integer`/`Standard_Boolean` typedefs with native C++ types in method signatures. Example — 7.x vs 8.0:

```cpp
// OCCT 7.x:
void BSplCLib::Eval(const Standard_Real U, Standard_Integer& Idx, Standard_Real& V);

// OCCT 8.0:
void BSplCLib::Eval(const double U, int& Idx, double& V);
```

pywrap's byref-output detection (which turns `Foo(T&)` into `Foo() -> T` in Python) matched on the OCCT typedef names. After 8.0 it sees `double&`/`int&`/`bool&` which weren't in the list, so the byref splitter skipped them and generated methods with non-Pythonic `&`-taking signatures that users can't call naturally.

**ocp.toml**

```diff
- byref_types = ["Standard_Real","Standard_Integer","Standard_Boolean"]
+ byref_types = ["double","int","bool"]
```

### Why `byref_types` is a config list, not hard-coded

The set of primitive-like types OCCT treats as "output parameters via reference" is an OCCT API convention, not a C++ language feature. It has changed before (the `Standard_*` typedefs themselves were a convention) and could change again. Keeping `byref_types` in `ocp.toml` means future migrations can adjust this list without touching pywrap code.

---

## 2.3 Missing `std::` prefix on bare std types

`[7.9-to-8rc3]`

Clang's pretty-printer drops the `std::` prefix on certain types. The existing regex fix in `_underlying_type()` already handled `optional`, `shared_ptr`, etc. OCCT 8.0's new Math modules additionally use `std::complex`.

**pywrap/bindgen/header.py** — `_underlying_type()`, `_std_types` tuple

```diff
  _std_types = (
      "optional", "reference_wrapper", "pair", "tuple",
      ...
-     "initializer_list",
+     "initializer_list", "complex",
  )
```

---

# 3 Template / typedef infrastructure

## 3.1 Register `_H` typedefs as template instantiations

`[7.9-to-8rc3]`

The `_H` name filter was correct for OCCT 7.x (where `_H` types were `DEFINE_HARRAY1` macro classes) but wrong for OCCT 8.0 where they are plain typedefs. Removing it registers ~260 missing template instantiations (`HArray1`, `HArray2`, `HSequence`).

Replaced with a targeted `NCollection_Shared` filter since no `register_template_NCollection_Shared` function exists.

**pywrap/bindgen/template_sub_pre.j2** — preregister block

```diff
- {% if not el.pod and not "_H" in el.name and el.template_base.__len__()>0 and not el.type.startswith("opencascade::handle") %}
+ {% if not el.pod and el.template_base.__len__()>0 and not el.type.startswith("opencascade::handle") and not el.type.startswith("occ::handle") and not el.type.startswith("handle<") and not el.type.startswith("Handle(") and el.template_base[0] != "NCollection_Shared" %}
```

**pywrap/bindgen/template_sub.j2** — register block

```diff
- {% if not td.pod and not "_H" in td.name and td.template_base.__len__()>0 and not td.type.startswith("opencascade::handle") %}
+ {% if not td.pod and td.template_base.__len__()>0 and not td.type.startswith("opencascade::handle") and not td.type.startswith("occ::handle") and not td.type.startswith("handle<") and not td.type.startswith("Handle(") and td.template_base[0] != "NCollection_Shared" %}
```

**pywrap/bindgen/\_\_init\_\_.py** — template filter

```diff
              if not t.pod
-             and not "_H" in t.name
              and len(t.template_base) > 0
              and not t.type.startswith("opencascade::handle")
+             and t.template_base[0] != "NCollection_Shared"
```

---

## 3.2 Template base class inheritance (HArray1, HArray2, HSequence)

`[7.9-to-8rc3]`

In OCCT 7.x, H-types were defined via `DEFINE_HARRAY1`/`DEFINE_HARRAY2`/`DEFINE_HSEQUENCE` macros that generated classes with their own method bodies. In OCCT 8.0, these became simple typedefs of `NCollection_HArray1<T>` / `NCollection_HArray2<T>` / `NCollection_HSequence<T>`, which only define constructors and rely entirely on inheritance from their base templates (`NCollection_Array1<T>`, `NCollection_Array2<T>`, `NCollection_Sequence<T>`) for all useful methods (`SetValue`, `Value`, `Length`, etc.).

The `super` macro only checked `all_classes` and `all_typedefs` when building the pybind11 base class list. Template base classes like `NCollection_Array1<TheItemType>` were silently dropped because the parameterized name isn't in either dict. Without the base class declared in `py::class_<>`, H-type pybind11 objects have no methods and polymorphism (passing an HArray1 where Array1 is expected) doesn't work.

The fix has three parts:

**A. Whitelist**: Not all template base classes can be included — many class templates inherit from other templates (e.g. `NCollection_Array2 : NCollection_Array1`, `BOPTools_BoxSelector : BVH_Traverse`) but not all instantiations have matching registered types. Template base classes are stripped by default; only explicitly configured ones are kept.

**B. `check_templates` flag**: The `super` macro gets a new flag so it can match surviving template base entries against `all_class_templates`. Only enabled for class template registration (`template_templates.j2`), not for regular classes.

**C. Toposort**: When an HArray1 typedef declares `NCollection_Array1<TheItemType>` as base, the matching Array1 typedef must be registered first. The existing toposort used raw template parameter names which don't match any DAG node. A reverse map resolves template superclass references to actual typedef names.

### Code changes

**pywrap/bindgen/\_\_init\_\_.py** — build `all_class_templates` dict and pass to Jinja2

```diff
      all_classes = {c.name: c for m in modules for c in m.classes}
      all_enums = {e.name: e for m in modules for e in m.enums}
      all_typedefs = {t.name: t for m in modules for t in m.typedefs}
+     all_class_templates = {
+         t.name: t for m in modules for t in m.class_templates
+     }
```

```diff
              "all_typedefs": all_typedefs,
+             "all_class_templates": all_class_templates,
              "project_name": name,
```

**pywrap/bindgen/\_\_init\_\_.py** — strip template base classes unless whitelisted (in `transform_module`)

```diff
+         # strip template base classes unless explicitly whitelisted
+         for ct in m.class_templates:
+             keep = set(s["Templates"].get(ct.name, {}).get("include_superclass_templates", []))
+             ct.superclass = [
+                 sup for sup in ct.superclass
+                 if "<" not in sup or sup.split("<")[0] in keep
+             ]
```

**pywrap/bindgen/\_\_init\_\_.py** — toposort: resolve template base deps to typedef names (in `render`)

The `typedef_by_tmpl` reverse map resolves `(template_name, args)` tuples to actual typedef names. The lookup uses the global `all_class_templates` (not the per-module `class_templates`) because typedefs like `ChFiDS_HData` reference class templates (`NCollection_HSequence`) defined in a different module (`NCollection`).

```diff
+             # map (template_name, args) -> typedef_name for resolving
+             # template superclass dependencies to actual typedef names
+             typedef_by_tmpl = {}
+             for el in classes_typedefs.values():
+                 if not isinstance(el, ClassInfo) and len(el.template_base) > 0:
+                     typedef_by_tmpl[(el.template_base[0], tuple(el.template_args))] = el.name

              dag = {}
              for el in classes_typedefs.values():
                  if isinstance(el, ClassInfo):
                      deps = set(el.superclass)
                  else:
                      base = el.template_base[0]
                      deps = set(el.template_args)
+                     if base in all_class_templates:
+                         for sup in all_class_templates[base].superclass:
+                             if "<" in sup:
+                                 sup_tmpl = sup.split("<")[0]
+                                 key = (sup_tmpl, tuple(el.template_args))
+                                 if key in typedef_by_tmpl:
+                                     deps.add(typedef_by_tmpl[key])
+                             else:
+                                 deps.add(sup)
                  dag[el.name] = deps
```

**pywrap/bindgen/schemas.py** — add `include_superclass_templates` to template config

```diff
- template_schema = Schema({Optional("exclude_constructors", default=[]): [int]})
+ template_schema = Schema({
+     Optional("exclude_constructors", default=[]): [int],
+     Optional("include_superclass_templates", default=[]): [str],
+ })
```

**pywrap/bindgen/macros.j2** — add `check_templates` flag to `super` macro

```diff
- {%- macro super(cls,classes,typedefs) -%}
-     {% for super in cls.superclass if super in classes or super in typedefs %}, {{super}} {% endfor %}
+ {%- macro super(cls,classes,typedefs,check_templates=false) -%}
+     {% for super in cls.superclass if super in classes or super in typedefs or (check_templates and super.split('<')[0] in all_class_templates) %}, {{super}} {% endfor %}
  {%- endmacro -%}
```

**pywrap/bindgen/template_templates.j2** — enable `check_templates` on both `preregister` and `register`

```diff
  void preregister_template_{{t.name}}(py::object &m, const char *name){
-     py::class_<... {{super(t,all_classes,all_typedefs)}}>(m,name,...);
+     py::class_<... {{super(t,all_classes,all_typedefs,check_templates=true)}}>(m,name,...);
  }
  void register_template_{{t.name}}(py::object &m, const char *name){
-     static_cast<py::class_<... {{super(t,all_classes,all_typedefs)}}>>(m.attr(name))
+     static_cast<py::class_<... {{super(t,all_classes,all_typedefs,check_templates=true)}}>>(m.attr(name))
```

**ocp.toml** — whitelist template base classes for HArray/HSequence types

```diff
+ [Modules.NCollection.Templates.NCollection_HArray1]
+     include_superclass_templates = ["NCollection_Array1"]
+
+ [Modules.NCollection.Templates.NCollection_HArray2]
+     include_superclass_templates = ["NCollection_Array2"]
+
+ [Modules.NCollection.Templates.NCollection_HSequence]
+     include_superclass_templates = ["NCollection_Sequence"]
```

**ocp.toml** — exclude `Storage_HArrayOfSchema` (no matching Array1 typedef)

In OCCT 8.0, `Storage_ArrayOfSchema.hxx` was gutted to a forward declaration — no typedef. `Storage_HArrayOfSchema` is the only HArray1 typedef without a matching Array1 registration.

```diff
- exclude_typedefs = ["Storage","Storage_MapOfCallBack","Storage_MapOfPers"]
+ exclude_typedefs = ["Storage","Storage_MapOfCallBack","Storage_MapOfPers","Storage_HArrayOfSchema"]
```

---

## 3.3 `NCollection_*::Contained` — pybind11 cast failure

`[7.9-to-8rc3]`

All NCollection container `Contained()` methods return `std::optional<std::reference_wrapper<const T>>` (or a pair of them). Pybind11 cannot cast `std::reference_wrapper<const opencascade::handle<U>>` — the `type_caster` tries to pass a pointer where a reference is expected. Additionally, `NCollection_IndexedDataMap::Contained` has an upstream OCCT rc5 bug (calls `aNode->Key()` but `IndexedDataMapNode` only has `Key1()`).

Users can use `Contains()` + `Find()` / `ChangeFind()` instead.

A duplicate TOML key also had to be fixed: two `exclude_class_template_methods` assignments for `[Modules.NCollection]` — the second silently overwrote the first.

The `NCollection_List::NCollection_List` constructor exclusion kept from the earlier list is for the `std::initializer_list<T>` overload that OCCT 8.0 added — pybind11 can't bind it because the arg type isn't a registered C++ type.

**ocp.toml** — `[Modules.NCollection]`

```diff
  exclude_class_template_methods = [".*::begin", ".*::end", ".*::cbegin", ".*::cend",
-     "NCollection_IndexedDataMap::Contained",
+     ".*::Contained",
      "NCollection_List::NCollection_List"]
- exclude_class_template_methods = [".*::begin", ".*::end", ".*::cbegin", ".*::cend"]
```

---

## 3.4 `NCollection_*::Bound`, `Seek`, `ChangeSeek` exclusions

`[8rc3-to-8rc5]`

Same mechanism as the `Contained` fix in section 3.3, but for different methods. These NCollection template methods return `handle<T>*` (pointer-to-handle), which pybind11 cannot cast.

**ocp.toml** — `exclude_class_template_methods`

```diff
  exclude_class_template_methods = [
      ...
+     ".*::Bound",
+     ".*::Seek",
+     ".*::ChangeSeek",
  ]
```

---

## 3.5 C++ `using` aliases and namespace-scoped class templates

`[8rc3-to-8rc5]`

OCCT 8.0 replaces many formerly-concrete classes with `using` type aliases to namespace- and class-scoped class template instantiations. Examples:

```cpp
// Namespace-scoped template:
namespace BRepGraph_DefsIterator {
  template <typename TraitsT> class DefsOfParent { ... };
}
using BRepGraph_DefsWireOfFace =
    BRepGraph_DefsIterator::DefsOfParent<WireOfFaceTraits>;

// Class-scoped template:
class BRepGraph_NodeId {
  enum class Kind { ... };
  template <Kind TheKind> struct Typed { ... };
};
using BRepGraph_FaceId = BRepGraph_NodeId::Typed<BRepGraph_NodeId::Kind::Face>;
```

Without the changes below, these aliases were either silently dropped (pywrap's `get_typedefs` only looked for `TYPEDEF_DECL`) or produced non-compilable C++ (bare template names with no enclosing scope). ~99 aliases across `Extrema`, `BRepLProp`, `GeomLProp`, `HLRBRep`, `Convert`, `BRepGraph`, `BRepGraphInc`, `math`, and other modules were affected.

### 3.5.1 Discover `using` aliases alongside `typedef`

**pywrap/bindgen/header.py** — `get_typedefs()`

```diff
  def get_typedefs(tu):
-     return get_symbols(tu, CursorKind.TYPEDEF_DECL)
+     return chain(
+         get_symbols(tu, CursorKind.TYPEDEF_DECL),
+         get_symbols(tu, CursorKind.TYPE_ALIAS_DECL),
+     )
```

### 3.5.2 Discover nested class templates

Class templates defined inside classes/structs (not just namespaces) need to be discovered so their registrar functions are emitted.

**pywrap/bindgen/header.py** — `get_class_templates()`

```diff
  def get_class_templates(tu):
-     return get_symbols(tu, CursorKind.CLASS_TEMPLATE)
+     return get_symbols(
+         tu, CursorKind.CLASS_TEMPLATE,
+         search_in=(CursorKind.NAMESPACE, CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL),
+     )
```

### 3.5.3 Track qualified names on `ClassTemplateInfo`

Three names are now tracked:

- `name` — fully qualified (`BRepGraph_NodeId::Typed`) — used in C++ type positions
- `bare_name` — unqualified (`Typed`) — for config pattern matching
- `registrar_name` — C++-identifier safe (`BRepGraph_NodeId_Typed`) — for function names

**pywrap/bindgen/header.py**

```python
def _enclosing_scope(cursor):
    """Walk class/struct/namespace parents, e.g. 'BRepGraph_NodeId'."""
    parts = []
    cur = cursor.semantic_parent
    while cur and cur.kind in (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL,
                               CursorKind.CLASS_TEMPLATE, CursorKind.NAMESPACE):
        if cur.spelling:
            parts.append(cur.spelling)
        cur = cur.semantic_parent
    return "::".join(reversed(parts))

class ClassTemplateInfo(ClassInfo):
    def __init__(self, cur):
        super().__init__(cur)
        self.bare_name = cur.spelling
        scope = _enclosing_scope(cur)
        self.name = (scope + "::" + cur.spelling) if scope else cur.spelling
        self.registrar_name = self.name.replace("::", "_")
        # Qualify non-type template parameter types (e.g. "Kind" -> "BRepGraph_NodeId::Kind")
        self.type_params = []
        for el, default in get_template_type_params(cur):
            type_spelling = el.type.spelling
            if scope and "::" not in type_spelling and el.spelling != type_spelling:
                type_spelling = scope + "::" + type_spelling
            type_kw = None if el.spelling == el.type.spelling else type_spelling
            self.type_params.append((type_kw, el.spelling, default))
```

### 3.5.4 Qualify template-base references in typedefs

`TypedefInfo.template_base` now uses qualified names so typedef → registrar matching works across qualified/unqualified contexts.

**pywrap/bindgen/header.py** — `TypedefInfo`

```python
for ch in cur.get_children():
    if ch.kind == CursorKind.TEMPLATE_REF:
        # get_definition() is safer than .referenced in multiprocessing
        defn = ch.get_definition()
        if defn is not None:
            scope = _enclosing_scope(defn)
            qname = (scope + "::" + ch.spelling) if scope else ch.spelling
            self.template_base.append(qname)
        else:
            self.template_base.append(ch.spelling)
```

`.referenced` causes bus errors in libclang's multiprocessing; `.get_definition()` is equivalent and stable.

### 3.5.5 Template code generation uses qualified/registrar names

**pywrap/bindgen/template_templates.j2** — registrar function names

```diff
- void preregister_template_{{t.name}}(py::object &m, const char *name) { ... }
+ void preregister_template_{{t.registrar_name}}(py::object &m, const char *name) { ... }
- void register_template_{{t.name}}(py::object &m, const char *name) { ... }
+ void register_template_{{t.registrar_name}}(py::object &m, const char *name) { ... }
```

**pywrap/bindgen/template_sub_pre.j2 / template_sub.j2** — registrar call sites

```diff
- preregister_template_{{ base }}{{ arg }}(m,"{{el.name}}");
+ preregister_template_{{ base|replace('::', '_') }}{{ arg }}(m,"{{el.name}}");
```

Dependency module extraction and template-arg extraction handle `::` correctly:

```diff
- {% set dep_module = td.type.split("_") %}
+ {% set base_for_module = td.template_base[0].split("::")[0] if td.template_base else td.type %}
+ {% set dep_module = base_for_module.split("_") %}

- {% set arg = td.type.split(td.template_base[0])[-1] %}
+ {% set bare_base = td.template_base[0].split("::")[-1] %}
+ {% set arg = td.type.split(td.template_base[0])[-1] if td.template_base[0] in td.type
+              else td.type.split(bare_base)[-1] %}
```

### 3.5.6 Method/arg type qualification in registrar bodies

libclang spells method signatures with the bare template name (e.g. `DefsOfParent<TraitsT>`), not the qualified one. The macros now also check `bare_name` as a fallback and replace with the qualified form.

**pywrap/bindgen/macros.j2** — `arg_type_with_template_params`, `template_return_type`

```jinja
{%- elif bare != template.name and bare + '<' in t -%}
    {% set ns.t = t|regex_replace(bare + '<[^>]+>', template.name + '<' + targs + '>') %}
```

A `regex_replace` filter was added to the Jinja environment in `pywrap/bindgen/__init__.py`. A new `argtypes_template` macro applies the same substitution to constructor arg lists (fixes bare `T` in e.g. `math_VectorBase`).

### 3.5.7 Const-correct `__iter__`

Some iterators have non-const `begin()`. The `__iter__` lambda now matches.

**pywrap/bindgen/template_templates.j2**

```diff
-         .def("__iter__",[](const {{t.name}}{{template_args(t)}} &self) { ... })
+         .def("__iter__",[]({{"const " if t.methods_dict["begin"].const}}{{t.name}}{{template_args(t)}} &self) { ... })
```

### 3.5.8 Exclusions

Most namespace-scoped templates (`BaseTraits`, `DefsOfParent`, `RefsOfParent`, `Typed`, `Usage`) now work via the qualified-name path. Only genuine non-bindable helpers remain excluded:

**ocp.toml**

```toml
[Modules.BRepGraph]
    exclude_class_templates = ["HasIsRemoved"]    # SFINAE trait (non-type second param)

[Modules.GeomLProp]
    exclude_class_templates = ["ToolAccess"]      # internal helper, no public typedefs
```

Exclusion now matches on both `name` (qualified) and `bare_name` for backward compatibility. Typedefs whose `template_base[0]` resolves (by qualified or bare name) to an excluded class template are also dropped — this prevents dangling registrar calls when the template itself isn't bound.

**pywrap/bindgen/\_\_init\_\_.py** — typedef filtering in `transform_module`

```python
# Exclude typedefs whose underlying template is itself excluded.
# Check both qualified name and bare name so config patterns like
# ["HasIsRemoved"] match BRepGraph_DefsIterator::HasIsRemoved.
excluded_bare = {n.rsplit("::", 1)[-1] for n in excluded_ct}
for h in m.headers:
    h.typedefs = [
        t for t in h.typedefs
        if not t.template_base
        or (t.template_base[0] not in excluded_ct
            and t.template_base[0].rsplit("::", 1)[-1] not in excluded_bare)
    ]
```

---

## 3.6 Typedef deduplication via union-find

`[8rc3-to-8rc5]`

pybind11 registers C++ types globally, so each type can only be `py::class_<>` registered once across all modules. OCCT 8.0 introduces two new collision patterns:

1. **Cross-module same-name duplicates** — e.g. `typedef NCollection_Vector<gp_XYZ> VectorOfPoint` defined identically in both `BRepBuilderAPI_VertexInspector.hxx` and `BRepExtrema_ProximityValueTool.hxx`. Same type, same Python name, different modules.
2. **Same-module aliases** — e.g. `Extrema_ExtPC` and `Extrema_ELPCOfLocateExtPC` both expand (after template-arg resolution) to the same `Extrema_GGExtPC<...>` instantiation despite different `type` spellings.

libclang's canonical type spelling (`Type.get_canonical().spelling`) is not reliable across parse contexts — for `math_VectorBase<double>` it is sometimes reported as `math_VectorBase<>` when template args haven't resolved. So neither `type` spelling alone nor `type_canonical` alone catches all cases.

**Solution**: union-find over all non-POD typedefs, where two are merged if they share their `type` spelling OR their `type_canonical`.

**pywrap/bindgen/header.py** — `TypedefInfo`

```diff
  self.type = t.spelling
+ self.type_canonical = t.get_canonical().spelling
  self.pod = t.is_pod()
```

**pywrap/bindgen/\_\_init\_\_.py** — dedup pass

```python
entries = [(m, h, t) for m in modules for h in m.headers
           for t in h.typedefs if not t.pod]

parent = list(range(len(entries)))
def find(x): ...
def union(a, b): ...

key_to_idx = {}
for i, (m, h, t) in enumerate(entries):
    for key in (t.type, t.type_canonical):
        if key in key_to_idx: union(i, key_to_idx[key])
        else: key_to_idx[key] = i

# Per group, shortest name wins:
# - same-module losers -> m.attr() alias emitted in template_sub.j2
# - cross-module losers -> silently removed (m.attr() is module-scoped)
```

**pywrap/bindgen/template_sub.j2** — emit same-module aliases before module close

```jinja
{% for alias_name, original_name in module.typedef_aliases %}
    m.attr("{{alias_name}}") = m.attr("{{original_name}}");
{% endfor %}
```

POD typedefs are skipped because they're never `py::class_<>` registered (`typedef char* BinObjMgt_PChar` and `typedef char* Standard_PCharacter` share canonical type `char *` but are unrelated).

Real-world effect across OCCT 8.0: 11 cross-module duplicate groups deduped (e.g. `VectorOfPoint` in 2 modules, `math_Vector` in 3, `NCollection_Vec2<float>` as both `Graphic3d_Vec2` and `gp_Vec2f`). Within Extrema, 8 same-type aliases collapse to shortest names with 8 `m.attr()` aliases.

---

# 4 Method / function signatures

## 4.1 `= default` constructors missing

`[7.9-to-8rc3]`

OCCT 8.0 marks many default constructors as `constexpr noexcept = default`:

```cpp
// OCCT 7.x:
class gp_Pnt {
public:
    gp_Pnt();   // explicit, has compiled body
};

// OCCT 8.0:
class gp_Pnt {
public:
    constexpr gp_Pnt() noexcept = default;   // compiler-generated, no library symbol
};
```

Compiler-generated defaulted constructors have no mangled name in the library — they're inlined at every call site. pywrap's `remove_undefined_mangled()` filter dropped them: their mangled name doesn't appear in the nm output, and the cursor isn't marked `inline`, so they looked like declarations without definitions. Result: `py::init<>()` for `gp_Pnt`, `gp_Dir`, `gp_Vec`, and dozens of other core types silently disappeared.

Fix: mark defaulted constructors as a special case that bypasses the symbol-table check. `py::init<>()` doesn't need a linker symbol anyway — pybind11 invokes the constructor inline at binding-registration time.

Uses `clang_CXXMethod_isDefaulted()` via `Cursor.is_default_method()`.

**pywrap/bindgen/header.py** — store `defaulted` flag on `ConstructorInfo`

```diff
  class ConstructorInfo(MethodInfo):
-     pass
+     defaulted: bool
+
+     def __init__(self, cur: Cursor):
+         super(ConstructorInfo, self).__init__(cur)
+         self.defaulted = cur.is_default_method()
```

**pywrap/bindgen/\_\_init\_\_.py** — keep defaulted constructors through symbol filtering

```diff
          c.constructors = [
              el
              for el in c.constructors
              if sym.name.str.endswith(el.mangled_name).any()
              or el.inline
              or el.pure_virtual
              or el.virtual
+             or el.defaulted  # = default ctors are compiler-generated; py::init<>() needs no symbol
          ]
```

---

## 4.2 Unbindable new method signatures

`[7.9-to-8rc3]`

New methods in OCCT 8.0 whose signatures pybind11 cannot handle. Each needs a targeted `exclude_methods` entry.

**`OpenGl_SetterInterface::Set`** — abstract method with a template parameter:

```cpp
// opengl/OpenGl_SetterInterface.hxx
class OpenGl_SetterInterface {
public:
    template <typename T>
    virtual void Set(const T& value) = 0;   // pybind11 cannot bind virtual templates
};
```

**`BRepTopAdaptor_FClass2d::Copy`** — returns a class with a deleted copy constructor:

```cpp
// BRepTopAdaptor_FClass2d.hxx
class BRepTopAdaptor_FClass2d {
    BRepTopAdaptor_FClass2d(const BRepTopAdaptor_FClass2d&) = delete;
public:
    BRepTopAdaptor_FClass2d Copy() const;  // return-by-value of non-copyable type
};
```

**ocp.toml**

```diff
  # [Modules.OpenGl] exclude_methods
+  "OpenGl_SetterInterface::Set"       # abstract setter with template parameter
```

```diff
+ [Modules.BRepTopAdaptor]
+     exclude_methods = ["BRepTopAdaptor_FClass2d::Copy"]  # return type has deleted copy ctor
```

Note: `RWGltf_GltfJsonParser::SetStream` (`std::istream&&`) was previously excluded here but is now handled by the generic rvalue-reference filter (section 4.3).

### Why these are one-off exclusions rather than a generic filter

Both exclusions target patterns that — unlike `T&&` parameters (section 4.3) — are rare enough not to warrant a generic filter:

- **Virtual + template parameter** appears once in 8.0 (`OpenGl_SetterInterface::Set`). It's a C++ language-level limitation (virtual functions cannot be templates), not a pybind11 quirk, and it has no obvious workaround besides exclusion.
- **Return-by-value of a non-copyable type** appears in exactly one method (`BRepTopAdaptor_FClass2d::Copy`). A generic filter scanning for deleted copy constructors on return types is possible but would add per-method AST inspection cost to every binding; the payoff of one saved exclusion entry doesn't justify it.

If either pattern proliferates in future OCCT releases, promoting one to a generic filter would be the natural next step — mirroring how 4.3 was generalized from per-method exclusions.

---

## 4.3 Move-assignment `operator=(T&&)` → generic rvalue-reference filter

`[7.9-to-8rc3]` (initial per-class exclusions) + `[8rc3-to-8rc5]` (generic filter)

pybind11 cannot bind signatures taking rvalue references (`T&&`). Python values are always lvalues — there's no syntax for "this will be consumed, don't use it afterwards" at the Python level, so pybind11 refuses to wrap signatures that demand rvalue-ness.

Two distinct OCCT 8.0 patterns produce `T&&` parameters:

```cpp
// 1. Move-assignment — universal, appears on most value types:
class TCollection_AsciiString {
    TCollection_AsciiString& operator=(TCollection_AsciiString&& other) noexcept;
};

// 2. Rvalue-only sink parameters — new in 8.0, appears on several setters:
class BOPAlgo_Builder {
    void SetArguments(TopTools_ListOfShape&& theArgs);   // takes ownership
};
class BRepAlgoAPI_BooleanOperation {
    void SetImages(NCollection_DataMap<TopoDS_Shape, TopTools_ListOfShape>&& theImages);
};
```

### Initial per-class exclusions `[7.9-to-8rc3]`

The first pass excluded the known move-assignment cases:

```diff
  [Modules.TCollection]
-     exclude_methods = ["TCollection_ExtendedString::ToUTF8CString"]
+     exclude_methods = ["TCollection_ExtendedString::ToUTF8CString",
+                        "TCollection_AsciiString::operator=",
+                        "TCollection_ExtendedString::operator="]

+ [Modules.math]
+     exclude_methods = ["math_Matrix::operator="]
```

### Generic filter `[8rc3-to-8rc5]`

When 8.0 rc5 added more `T&&` sinks (`SetArguments`, `SetImages`, etc.), chasing each in `ocp.toml` stopped being scalable. A single filter in the transform phase drops any method/function whose argument list contains ` &&`:

**pywrap/bindgen/\_\_init\_\_.py** — transform phase

```diff
+ def _has_rvalue_ref(method):
+     return any(" &&" in t for _, t, _ in method.args)
+
  for m in modules:
      for c in m.classes:
-         # (no rvalue filter — relied on ocp.toml exclude_methods)
+         c.methods        = [m_ for m_ in c.methods        if not _has_rvalue_ref(m_)]
+         c.static_methods = [m_ for m_ in c.static_methods if not _has_rvalue_ref(m_)]
+         c.operators      = [m_ for m_ in c.operators      if not _has_rvalue_ref(m_)]
+     for ct in m.class_templates:
+         ct.methods        = [m_ for m_ in ct.methods        if not _has_rvalue_ref(m_)]
+         ct.static_methods = [m_ for m_ in ct.static_methods if not _has_rvalue_ref(m_)]
+         ct.operators      = [m_ for m_ in ct.operators      if not _has_rvalue_ref(m_)]
+     m.functions = [f for f in m.functions if not _has_rvalue_ref(f)]
```

The filter pattern is the literal string `" &&"` (space-ampersand-ampersand). That catches `T &&` (the canonical libclang spelling) without matching `&&` in other positions like inside template-args or expressions.

Once the generic filter is in place, the per-class `operator=` exclusions from the initial pass are redundant — the filter drops them automatically — but they're harmless to leave in the TOML (they just never match).

---

## 4.4 `T* const&` return type doubling

`[7.9-to-8rc3]`

`_underlying_type()` in `header.py` doubles the `const` for `T* const&` return types. `HLRBRep_TheCSFunctionOfInterCSurf::AuxillarSurface` returns `HLRBRep_Surface* const&`. Line 613: `pointee.is_const_qualified()` is true because the pointer is const, but the `const` variable gets placed as a leading qualifier (`const HLRBRep_Surface *const &`), incorrectly marking the pointed-to type as const. The actual type is `HLRBRep_Surface *const &`.

Fix: when pointee is itself a pointer/reference (`pointee.kind in KIND_DICT`), check what the pointer points to (`pointee.get_pointee().is_const_qualified()`) instead of the pointer's own constness. The pointer's const is already embedded in `pretty_printed` as `*const`.

Only one class in all of OCCT 8.0 uses this pattern: `HLRBRep_TheCSFunctionOfInterCSurf`.

**pywrap/bindgen/header.py** — `_underlying_type()`, line 613

```diff
-            const = " const " if pointee.is_const_qualified() else ""
+            if pointee.kind in self.KIND_DICT:
+                # pointee is itself a pointer/ref — check what IT points to,
+                # not the pointer's own const (already in pretty_printed as *const)
+                const = " const " if pointee.get_pointee().is_const_qualified() else ""
+            else:
+                const = " const " if pointee.is_const_qualified() else ""
```

---

## 4.5 Copy semantics check

`[7.9-to-8rc3]`

OCCT 8.0 has types that delete the copy constructor but keep copy-assignment — a pattern that supports "reset" semantics without allowing independent duplicates:

```cpp
// OCCT 8.0 pattern:
class BRepTopAdaptor_FClass2d {
    BRepTopAdaptor_FClass2d(const BRepTopAdaptor_FClass2d&) = delete;
    BRepTopAdaptor_FClass2d& operator=(const BRepTopAdaptor_FClass2d&);  // allowed
public:
    BRepTopAdaptor_FClass2d();
};

// Usage:
BRepTopAdaptor_FClass2d a;
BRepTopAdaptor_FClass2d b;
b = a;   // OK — assigns value
auto c = a;   // ERROR — copy constructor deleted
```

OCP's `__copy__` / `__deepcopy__` helper template used `std::is_copy_constructible<T>` to decide whether to emit a copy helper. For these types that test returns `false`, so no copy helper was generated — but Python users could (and did) expect `copy.copy(obj)` to work, because the type _is_ logically copyable via assignment.

Fix: check `std::is_copy_assignable<T>` instead. The helper constructs a default-initialized `T`, then assigns:

```cpp
// pseudocode of generated helper:
T copy_if_copy_assignable(const T& src) {
    if constexpr (std::is_copy_assignable<T>::value) {
        T dst;   // requires default constructor, which all affected types have
        dst = src;
        return dst;
    }
    return src;   // (fallback; only compiled when assignable, so unreachable in practice)
}
```

**OCP_specific.inc**

```diff
- if constexpr (std::is_copy_constructible<T>::value){
+ if constexpr (std::is_copy_assignable<T>::value){
```

---

## 4.6 `noexcept` propagation in trampoline classes

`[7.9-to-8rc3]`

C++17 makes `noexcept` part of the type system. A non-`noexcept` override of a `noexcept` virtual is ill-formed. OCCT 8.0's `BRepGraph_Layer` declares pure virtual callbacks as `noexcept`. Pywrap's trampoline generator didn't capture or emit the specifier.

**pywrap/bindgen/header.py** — import + `MethodInfo`

```diff
  from clang.cindex import (
      ...
+     ExceptionSpecificationKind,
  )
```

```diff
  class MethodInfo(FunctionInfo):
      const: bool
      virtual: bool
      pure_virtual: bool
+     noexcept: bool

      def __init__(self, cur: Cursor):
          ...
+         self.noexcept = (
+             cur.exception_specification_kind
+             == ExceptionSpecificationKind.BASIC_NOEXCEPT
+         )
```

**pywrap/bindgen/macros.j2** — `prototype` macro

```diff
- ){% if f.const %} const {%endif%}
+ ){% if f.const %} const {%endif%}{% if f.noexcept %} noexcept {%endif%}
```

---

# 5 Class structure

## 5.1 Nested enum value clash (`gp_Dir::D`)

`[7.9-to-8rc3]`

OCCT 8.0 added nested enum `gp_Dir::D` with values `X`, `Y`, `Z` which clash with existing methods `gp_Dir.X()`, `gp_Dir.Y()`, `gp_Dir.Z()`. Removing `.export_values()` from all nested enums avoids these collisions. Enum values remain accessible as `ClassName.EnumName_e.Value`.

**pywrap/bindgen/template_sub.j2**

```diff
-            .value("{{val}}", {{enum.name}}::{{val}}){{ ".export_values();" if loop.last }}
+            .value("{{val}}", {{enum.name}}::{{val}}){{ ";" if loop.last }}
```

---

## 5.2 Anonymous namespaces exposing internal classes

`[7.9-to-8rc3]`

OCCT 8.0 increasingly uses anonymous namespaces to hide implementation-detail classes:

```cpp
// Extrema_GGenExtCC.hxx
namespace {
    // Internal helper — not part of the public API:
    class Extrema_GGenExtCC_PointsInspector { ... };
}
```

libclang reports anonymous namespaces with an empty spelling (`""`). pywrap's `get_symbols` walks into every namespace child matching `search_in` kinds, which by default accepts empty spellings too. That caused internal classes to be discovered and bound — generating broken code (the classes aren't visible at global scope) and exposing implementation details.

Fix: skip children with empty spellings in the namespace descent.

**pywrap/bindgen/header.py**

```diff
              and child.kind in search_in
              and child.spelling not in exclude_ns
+             and child.spelling != ""
```

---

## 5.3 `Bnd_Box::Limits` nested struct — `references_inner` filter

`[7.9-to-8rc3]`

OCCT 8.0 added `Bnd_Box::Get()` returning a new nested `Bnd_Box::Limits` struct (6 doubles). `Bnd_Box2d` has the same pattern (4 doubles). pywrap does not register nested types, so these overloads fail at compile time.

The old by-ref `Get(double&,...)` overload must be preserved — it is used by build123d and cadquery. `exclude_methods` cannot solve this: it runs before the byref split (by design — several excluded methods like `AppCont_Function::PeriodInformation` and `BRepMesh_DataStructureOfDelaun::ElementNodes` are byref methods that must be excluded before extraction). Since `_exclude_methods` filters by name, `exclude_methods = ["Bnd_Box::Get"]` would kill ALL overloads, including the needed by-ref one.

Fix: apply the `references_inner` filter (already used in `template_templates.j2` for class template methods) to regular class methods in `template_sub.j2`. This lambda checks if a method's return type or argument types reference `ClassName::` (a nested type). Methods referencing nested types like `Bnd_Box::Limits` are silently skipped at template render time, while the by-ref `Get` overload (which uses plain `double&` args) passes through unaffected.

`Limits` is only referenced inside `Bnd_Box.hxx` and `Bnd_Box2d.hxx` themselves — no other OCCT 8.0 method takes or returns it, so skipping these overloads has zero downstream impact.

**pywrap/bindgen/template_sub.j2** — add `references_inner` filter to regular class methods

```diff
  // methods
- {% for m in c.methods %}
+ {% for m in c.methods if not references_inner(c.name, m) %}
  {% if not m.pointer_by_ref %}
```

No `ocp.toml` changes needed — `Bnd_Box::Get` and `Bnd_Box2d::Get` are NOT excluded.

---

## 5.4 `NCollection_` return value policy (segfaults)

`[7.9-to-8rc3]`

Methods returning `const NCollection_Array1<T>&` (e.g. `Poles()`, `Knots()`, `Multiplicities()`) segfaulted because the returned reference was not tied to the parent object's lifetime.

In OCCT 7.x, these methods returned `const TColgp_Array1OfPnt&` or `const TColStd_Array1OfReal&`. The `template_sub.j2` template had explicit checks for `"TColgp_"` and `"TColStd_"` in the return type to apply `py::return_value_policy::reference_internal`. In OCCT 8.0, the typedefs are gone — return types are now bare `NCollection_Array1<gp_Pnt>`, which no longer matched the old checks.

Without `reference_internal`, pybind11 copies the returned reference into a new Python object that outlives the C++ parent, leading to use-after-free segfaults on access.

Fix: add `"NCollection_"` to the return value policy condition.

**pywrap/bindgen/template_sub.j2** — `methods_return_byref` section, line 205

```diff
  {% if (not is_byref_smart_ptr(m.return_type) and not m.return_type.strip().startswith('const'))
        or "TColgp_" in m.return_type or "TColStd_" in m.return_type
+       or "NCollection_" in m.return_type %}
        , py::return_value_policy::reference_internal
  {% endif %}
```

Affected methods include `Geom_BSplineCurve::Poles()`, `Geom_BSplineCurve::Knots()`, `Geom_BSplineCurve::Multiplicities()`, `Geom_BezierCurve::Poles()`, `Geom_BezierCurve::Weights()`, and their `Geom2d_*` counterparts — any method returning `const NCollection_*<T>&`.

---

## 5.5 Bare nested type names in generated code

`[7.9-to-8rc3]`

Clang's pretty-printer and token extractor emit type names relative to their enclosing scope. That's correct _inside_ the class body, but pywrap uses those strings in generated binding code that lives at global scope — where the bare names are unresolved. Affects return types, argument types, and default argument values.

**Example** — OCCT 8.0 header:

```cpp
// In BRepGraph_ChildExplorer.hxx:
class BRepGraph_ChildExplorer {
public:
    enum class TraversalMode { Direct, Recursive };

    void SetMode(TraversalMode theMode = TraversalMode::Recursive);
    // libclang reports default value as the bare token "TraversalMode :: Recursive"
};
```

Without qualification, pywrap generates this — which doesn't compile because `TraversalMode` is not in scope at the binding-code call site:

```cpp
// GENERATED (broken):
cls.def("SetMode", &BRepGraph_ChildExplorer::SetMode,
    py::arg("theMode") = static_cast<TraversalMode>(TraversalMode :: Recursive));
//                       ^^^^^^^^^^^^^^^ unresolved at global scope
```

After qualification:

```cpp
// GENERATED (correct):
cls.def("SetMode", &BRepGraph_ChildExplorer::SetMode,
    py::arg("theMode") = static_cast<BRepGraph_ChildExplorer::TraversalMode>(
        BRepGraph_ChildExplorer::TraversalMode :: Recursive));
```

More examples of the same pattern: `Typed<Kind::Surface>` → `BRepGraph_RepId::Typed<BRepGraph_RepId::Kind::Surface>`; `Options()` → `BRepGraphInc_Populate::Options()`.

### Implementation

**pywrap/bindgen/header.py** — new `_qualify_nested_types()` static method on `FunctionInfo`

```python
@staticmethod
def _qualify_nested_types(cur, s):
    """Prefix bare nested names (enums/classes/structs/templates) in 's'
    with the enclosing scope (class or namespace) of 'cur'.
    Walks ancestor namespaces and resolves 'using namespace' directives.
    """
    parent = cur.semantic_parent
    while parent and parent.kind in (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL,
                                      CursorKind.CLASS_TEMPLATE, CursorKind.NAMESPACE):
        # collect nested enum/class/struct/template names directly inside `parent`
        nested = {ch.spelling for ch in parent.get_children()
                  if ch.kind in (CursorKind.ENUM_DECL, CursorKind.CLASS_DECL,
                                 CursorKind.STRUCT_DECL, CursorKind.CLASS_TEMPLATE)
                  and ch.spelling}
        scope = _full_scope_path(parent)
        for name in nested:
            # (?<![:\w]) prevents double-qualification of already-qualified names
            s = re.sub(rf'(?<![:\w])\b{re.escape(name)}\b', f'{scope}::{name}', s)
        # for namespaces, also collect names from all re-openings in the TU
        #   (each #include can re-open `namespace MathLin { ... }`; libclang
        #   sees those as separate cursors with the same spelling)
        parent = parent.semantic_parent
    return s
```

Called from:

- `MethodInfo.__init__()` — qualifies return types and arg types for class methods
- `FunctionInfo.__init__()` — qualifies return types, arg types, and default value types for namespace-level functions
- `_default_value(cur, method_cur)` — qualifies bare names in default argument token strings; the `method_cur` parameter was added so the helper can look up the enclosing scope of the *method* declaring the default, not the type cursor itself

```diff
- def _default_value(cur):
+ def _default_value(cur, method_cur):
      tokens = [...]
-     return tokens_to_str(tokens)
+     return FunctionInfo._qualify_nested_types(method_cur, tokens_to_str(tokens))
```

The `(?<![:\w])` negative lookbehind prevents turning an already-qualified `Foo::TraversalMode` into `Foo::Foo::TraversalMode` on repeat qualification passes.

---

## 5.6 `BRepGraphInc_Populate::Options` registration

`[8rc3-to-8rc5]`

`BRepGraphInc_Populate::Options` is a nested struct used as a default argument in public API methods of both `BRepGraph` and `BRepGraphInc`. pywrap's `get_symbols()` only descends into namespaces (not classes), so nested types are not discovered automatically. The type is registered manually via `include_body_pre`.

Placement matters: since modules load alphabetically, `BRepGraph` loads before `BRepGraphInc`, so the Options type must be registered in `BRepGraph`'s `include_body_pre` — not `BRepGraphInc`'s — to be available when default-arg resolution happens for both modules' methods.

**ocp.toml**

```toml
[Modules.BRepGraph]
    include_header_pre_top = "#include <BRepGraphInc_Populate.hxx>"
    include_body_pre = """
    py::class_<BRepGraphInc_Populate::Options>(m, "BRepGraphInc_Populate_Options")
        .def(py::init<>())
        .def_readwrite("ExtractRegularities", &BRepGraphInc_Populate::Options::ExtractRegularities)
        .def_readwrite("ExtractVertexPointReps", &BRepGraphInc_Populate::Options::ExtractVertexPointReps)
        .def_readwrite("CreateAutoProduct", &BRepGraphInc_Populate::Options::CreateAutoProduct);
"""
```

---

# 6 Parse context & exclusions

## 6.1 Namespace-based modules (Math\*, GeomEval, Geom2dEval, GeomBndLib)

`[7.9-to-8rc3]`

OCCT 8.0 introduced modules organized as C++ namespaces instead of classes: MathUtils, MathRoot, MathOpt, MathLin, MathSys, MathInteg, MathPoly, GeomEval, Geom2dEval, GeomBndLib. Pywrap was designed for class-based modules. Several changes were needed.

### 6.1.1 Full namespace path for function references

`FunctionInfo.namespace` stored only the immediate parent (`"detail"`). For nested namespaces like `MathPoly::detail`, the generated function pointer `&detail::Func` is unresolved at global scope. Now stores the full path (`"MathPoly::detail"`) by walking the semantic parent chain.

**pywrap/bindgen/header.py** — new `_full_namespace_path()` helper

```python
def _full_namespace_path(cursor):
    parts = []
    cur = cursor
    while cur and cur.kind == CursorKind.NAMESPACE:
        parts.append(cur.spelling)
        cur = cur.semantic_parent
    return "::".join(reversed(parts))
```

Used in `FunctionInfo.__init__()` and `HeaderInfo.namespaces` collection.

### 6.1.2 Nested namespace submodule creation

Templates updated to create nested Python submodules and use sanitized C++ variable names.

**pywrap/bindgen/template_sub_pre.j2** — submodule creation

```diff
- {% for ns in module.namespaces %}
- m.def_submodule("{{ns}}");
- {% endfor %}
+ {% for ns in module.namespaces|sort %}
+ {% set parts = ns.split("::") %}
+ {% if parts|length == 1 %}
+ m.def_submodule("{{ns}}");
+ {% elif parts|length == 2 %}
+ static_cast<py::module>(m.attr("{{parts[0]}}")).def_submodule("{{parts[1]}}");
+ {% endif %}
+ {% endfor %}
```

**pywrap/bindgen/template_sub.j2** — namespace module variables + function binding

```diff
- auto m{{ns}} = static_cast<py::module>(m.attr("{{ns}}"));
+ // for single-level: auto mMathPoly = m.attr("MathPoly")
+ // for nested:       auto mMathPoly_detail = mMathPoly.attr("detail")
```

```diff
- {{ "m" + (f.namespace or "") }}.def(...)
+ {{ "m" + ((f.namespace or "")|replace("::", "_")) }}.def(...)
```

### 6.1.3 Nested abstract class trampoline names

Classes with `::` in their name (e.g. `GeomEval_RepCurveDesc::Base`) produced invalid trampoline identifiers like `Py_GeomEval_RepCurveDesc::Base`. Fixed by replacing `::` with `_`.

**pywrap/bindgen/macros.j2** — `trampoline_class` macro

```diff
- class Py_{{c.name}} : public {{c.name}}{
-     using {{c.name}}::{{c.name}};
+ class Py_{{c.name|replace("::", "_")}} : public {{c.name}}{
+     using {{c.name}}::{{c.name.split("::")[-1]}};
```

Same `|replace("::", "_")` applied to `Py_` references in `template_sub_pre.j2` (line 111) and `template_sub.j2` (line 99).

---

## 6.2 Forward declaration resolution — DE\* and Geom modules

`[7.9-to-8rc3]`

Several new OCCT 8.0 modules use forward declarations in base class headers that pybind11 needs as complete types. Added `include_header_pre_top` entries.

**ocp.toml**

```toml
# DE* modules: DE_ConfigurationNode.hxx and DE_Provider.hxx forward-declare these
[Modules.DEBREP]  # (and DEIGES, DEOBJ, DEPLY, DESTEP, DESTL, DEVRML, DEXCAF)
    include_header_pre_top = """#include <DE_ConfigurationContext.hxx>
#include <NCollection_Buffer.hxx>
#include <TopoDS_Shape.hxx>
#include <XSControl_WorkSession.hxx>
#include <TDocStd_Document.hxx>"""

# Geom/Geom2d: nested types from GeomEval/Geom2dEval
[Modules.Geom]
    include_header_pre_top = """#include <GeomEval_RepCurveDesc.hxx>
#include <GeomEval_RepSurfaceDesc.hxx>"""

[Modules.Geom2d]
    include_header_pre_top = "#include <Geom2dEval_RepCurveDesc.hxx>"
```

Also copied `GeomBndLib_InfiniteHelpers.pxx` to `/opt/local/occt-master/include/opencascade/` (`.pxx` files are not installed by OCCT's cmake install but are referenced by installed headers).

---

## 6.3 OCCT rc5 bugs and unbindable namespace functions

`[8rc3-to-8rc5]`

Three OCCT rc5 issues required workarounds. Two are genuine upstream bugs; one is a C++ language limitation pybind11 inherits.

### MathLin eigen functions — two overlapping issues

```cpp
// MathLin_Jacobi.hxx (OCCT 8.0 rc5, abridged):
namespace MathLin {
  struct EigenResult { math_Matrix Vectors; math_Vector Values; };
}
namespace MathUtils {
  struct EigenResult { math_Matrix Vectors; math_Vector Values; size_t NbIterations; };
}

namespace MathLin {
  using namespace MathUtils;   // (A) ambiguity trap

  EigenResult Jacobi(const math_Matrix& A, ...) {
    EigenResult aResult = ...;
    aResult.NbIterations = static_cast<size_t>(aNbRotations);  // (B) bug
    return aResult;
  }
}
```

**(A) `using namespace MathUtils`** means both `MathLin::EigenResult` and `MathUtils::EigenResult` are visible inside `MathLin`. libclang resolves the bare return type to `MathUtils::EigenResult` (the imported one), so pywrap generates `MathUtils::EigenResult Jacobi(...)` bindings — but `Jacobi`'s *definition* returns a `MathLin::EigenResult`. Mismatch, link/compile fails downstream.

**(B) OCCT rc5 bug**: `MathLin::EigenResult` doesn't have `NbIterations` (that's the `MathUtils` version), so the line `aResult.NbIterations = ...` doesn't compile at all. Upstream will fix this; until then we patch the header.

Excluding the three Eigen-returning functions (`Jacobi`, `EigenValues`, `SpectralDecomposition`) sidesteps the binding problem. Patching the header fixes the compile.

### MathSys — fixed-size array pointer parameters

```cpp
// MathSys.hxx
namespace MathSys::detail {
  bool Solve3x3(const double (*A)[3], const double* b, double* x);
  bool Solve4x4(const double (*A)[4], const double* b, double* x);
}
```

The parameter type `const double(*)[3]` is a pointer to a fixed-size array. pybind11's type_caster has no facility for building these from Python — there's no natural Python value that means "pointer to array of exactly 3 doubles" (even NumPy arrays are dynamic). Not a bug, just unbindable. Users who need this call the higher-level `math_Matrix::Solve()` which takes dynamic sizes.

**ocp.toml**

```toml
[Modules.MathLin]
    # MathLin::EigenResult != MathUtils::EigenResult (different structs).
    # Clang resolves return type via 'using namespace MathUtils'.
    # MathLin_Jacobi.hxx:90 also has upstream bug (NbIterations field missing).
    exclude_functions = ["Jacobi", "EigenValues", "SpectralDecomposition"]

[Modules.MathSys]
    # detail::Solve3x3/Solve4x4 take const double(*)[N] — pybind11 can't cast
    # fixed-size array pointers
    exclude_functions = ["Solve3x3", "Solve4x4"]
```

**opencascade/MathLin_Jacobi.hxx** — patched line 90

```diff
- aResult.NbIterations = static_cast<size_t>(aNbRotations);
+ // OCP patch: MathLin::EigenResult has no NbIterations (OCCT rc5 bug)
+ // aResult.NbIterations = static_cast<size_t>(aNbRotations);
```

Comment out rather than delete so the diff is obviously a workaround that can be reverted once OCCT fixes the upstream struct definition.

---

## 6.4 New namespace/class exclusions

`[7.9-to-8rc3]`

OCCT 8.0 introduced internal namespaces and classes that must not be bound. Each exclusion has a specific reason — useful context when more internal helpers appear in future OCCT releases.

**`NCollection_ItemsView`** — range-helper namespace containing only iterator glue (e.g. `Begin`, `End` templates used for `NCollection_Map::ItemsView()`). Not meaningful in Python where iteration is handled via `__iter__`.

**`NCollection_ForwardRangeDetail`** — C++20-style range support internals (`ForwardRangeIterator`, `ForwardRangeSentinel`). Users get Python iteration via the `__iter__` binding in `template_templates.j2`.

**`NCollection_ForwardRange`** — the class that goes with the detail namespace above. Template base only, no user-facing API.

**`Standard_ErrorHandler::Abort` / `::Error`** — these use `noreturn` attribute and interact with OCCT's internal `setjmp`/`longjmp`-based signal handling. Calling them from Python would abort the interpreter or leave the stack in an undefined state.

**ocp.toml** — `exclude_namespaces`

```diff
  exclude_namespaces = [
    ...
+   "NCollection_ItemsView",
+   "NCollection_ForwardRangeDetail",
  ]
```

**ocp.toml** — `[Modules.NCollection]` `exclude_classes`

```diff
  exclude_classes = ["NCollection","NCollection_ListNode",
+     "NCollection_ForwardRange"]
```

**ocp.toml** — `[Modules.Standard]` `exclude_methods`

```diff
  exclude_methods = [...
+     "Standard_ErrorHandler::Abort", "Standard_ErrorHandler::Error"]
```

### Why each exclusion carries its own rationale

"It breaks pybind11" is rarely the whole story. Each of the four exclusions above fits one of several recognizable patterns:

- **Internal implementation detail** (no public API role) — `NCollection_ItemsView`, `NCollection_ForwardRange` sit in the first pattern.
- **`noreturn` / signal-interacting** (dangerous from Python regardless of bindability) — `Standard_ErrorHandler::Abort`/`::Error`.
- **Template or metaprogramming helper with no runtime semantics** — `NCollection_ForwardRangeDetail`.
- **Abstract class with no useful polymorphic binding** — none in this group, but common enough to be worth naming.

These categories are the shape of the reasoning behind the choices in section 6.4, not a prescription for future work. When OCCT's internal structure changes, the categories themselves may need to be extended.

---

## 6.5 Parse context fixes for remaining modules

`[8rc3-to-8rc5]`

Several modules had parse warnings or errors because their headers use types not visible when parsed in isolation. Each `parsing_headers` entry prepends a `#include` (or forward declaration) to the specified header so libclang sees the types it needs.

**ocp.toml**

```toml
[Modules.NCollection.parsing_headers]
    "NCollection_PackedMapAlgo.hxx" = "#include <NCollection_PackedMap.hxx>"

[Modules.Extrema.parsing_headers]
    "Extrema_GLocateExtPC.hxx" = "#include <GeomAbs_Shape.hxx>"
    "Extrema_GGExtPC.hxx"      = "#include <GeomAbs_Shape.hxx>"

[Modules.Geom2dGridEval.parsing_headers]
    "Geom2dGridEval_Line.hxx" = "#include <gp_Lin2d.hxx>"

[Modules.GeomGridEval.parsing_headers]
    "GeomGridEval_Line.hxx" = "#include <gp_Lin.hxx>"

[Modules.OpenGl.parsing_headers]
    "OpenGl_LayerList.hxx"         = "#include <OpenGl_FrameBuffer.hxx>"
    "OpenGl_ShaderObject.hxx"      = "#include <NCollection_Sequence.hxx>"
    "OpenGl_BufferCompatT.hxx"     = "#include <Graphic3d_Buffer.hxx>"
    "OpenGl_VertexBufferCompat.hxx" = "#include <Graphic3d_Buffer.hxx>"
    "OpenGl_SetOfShaderPrograms.hxx" = "#include <TCollection_AsciiString.hxx>"
    "OpenGl_ShaderProgram.hxx"     = "class OpenGl_ShaderProgram;"
```

The `OpenGl_ShaderProgram.hxx` entry is a forward declaration rather than an include — the real header includes itself transitively, so a full include would cycle. The forward declaration is enough for pywrap to parse types that mention `OpenGl_ShaderProgram*`.

Also related — exclusions for iterator typedefs inside OpenGl classes whose names collide across parent classes (libclang reports them by bare spelling):

```toml
[Modules.OpenGl]
    exclude_typedefs = [..., "StructIterator", "GroupIterator"]

[Modules.TObj]
    exclude_typedefs = [..., "Iterator"]
```

These were in addition to the entries documented in sections 6.1–6.2.

---

# 7 Warning suppression

## 7.1 Suppress `#pragma message` warnings (pywrap parse)

`[7.9-to-8rc3]`

OCCT 8.0 headers emit deprecation `#pragma message` directives that clutter the pywrap parse output. Example header:

```cpp
// TColStd_ListOfInteger.hxx
Standard_HEADER_DEPRECATED("TColStd_ListOfInteger.hxx is deprecated since OCCT 8.0.0. "
                            "Use NCollection_List<int> directly")
```

`Standard_HEADER_DEPRECATED` expands to `#pragma message(...)`. At parse time this produces thousands of lines of noise:

```
dummy.cxx:3:4: warning: TColStd_ListOfInteger.hxx is deprecated since OCCT 8.0.0...
```

These are informational, not actionable — OCP must bind the deprecated headers for backward compatibility. Silence them at parse time with `-Wno-#pragma-messages`. `-Wno-deprecated-declarations` (already present) silences the `__attribute__((deprecated))` markers on the actual symbols; the new flag silences the file-level header pragma messages.

**pywrap/bindgen/translation_unit.py**

```diff
      "-std=c++17",
      "-D__CODE_GENERATOR__",
      "-Wno-deprecated-declarations",
+     "-Wno-#pragma-messages",
```

Note: this is a _parse-time_ flag for libclang. The _compile-time_ equivalents are in section 7.2 / 8.3.

---

## 7.2 Suppress compilation warnings

`[8rc3-to-8rc5]`

The build produced 814 warnings in two categories:

**Deprecated-declarations (734 warnings):** OCCT 8.0 deprecated many typedefs (`TopTools_ListOfShape`, `Standard_Boolean`, etc.), NCollection_Map methods, and entire classes (`GProp_CelGProps`, `Standard_Mutex`). These are unavoidable since OCP must bind these names for backward compatibility.

Fix: added `-Wno-deprecated-declarations` to the compile flags (see section 8.3 for the CMake property issue that had to be fixed first).

**Unused-value (80 warnings):** pywrap emits `static_cast<py::class_<...>>(klass)` blocks for class bindings. When a class has no bindable members, the expression result is unused.

Fix: prepend `(void)` cast in both templates.

**pywrap/bindgen/template_sub.j2**

```diff
-    static_cast<py::class_<...>>(klass)
+    (void)static_cast<py::class_<...>>(klass)
```

**pywrap/bindgen/template_templates.j2** — same `(void)` cast for template classes.

---

# 8 macOS Build Environment

## 8.1 RapidJSON CMake variable case

`[7.9-to-8rc3]`

OCCT 8.0 changed the CMake variable name to uppercase.

**CMakeLists.txt**

```diff
-        -i ${RapidJSON_INCLUDE_DIRS}
+        -i ${RAPIDJSON_INCLUDE_DIRS}
```

---

## 8.2 macOS ARM clang include path handling

`[7.9-to-8rc3]`

The pywrap parse phase needs correct system include paths for clang. The old hardcoded paths (clang 6/8/9/10, conda `include/c++/v1/`) conflicted with Xcode SDK libc++ on ARM Mac. Replaced with dynamic SDK and resource-dir detection.

**pywrap/bindgen/translation_unit.py** — macOS-specific args

```diff
+ import sys
+ from pathlib import Path
+ from .utils import current_platform

+ if not prefix and current_platform() == "OSX":
+     sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
+     args.append("-isysroot")
+     args.append(sdk)
+     clang_res = Path(sys.prefix) / "lib" / "clang"
+     if clang_res.is_dir():
+         for ver in sorted(clang_res.iterdir(), reverse=True):
+             if (ver / "include").is_dir():
+                 args.append("-resource-dir")
+                 args.append(str(ver))
+                 break
```

**pywrap/bindgen/utils.py** — `get_includes()`: removed hardcoded paths

```diff
- rv.append(Path(prefix) / "lib/clang/8.0.0/include/")
- rv.append(Path(prefix) / "lib/clang/6.0.1/include/")
- rv.append(Path(prefix) / "lib/clang/9.0.1/include/")
- rv.append(Path(prefix) / "lib/clang/10.0.1/include/")
- rv.append(Path(prefix) / "include/c++/v1/")
+ # On non-Windows without prefix: no auto-added includes
+ # (handled by -isysroot in translation_unit.py)
```

**ocp.toml** — `[OSX]` section

```diff
  [OSX]
      modules = ["Cocoa"]
      symbols = "symbols_mangled_mac.dat"
-     prefix = "/Library/Developer/CommandLineTools/SDKs/MacOSX10.15.sdk/usr"
-     includes = ["/opt/local/include/gcc8/c++/","/opt/local/lib/gcc8/gcc/x86_64-apple-darwin18/8.3.0/include"]
+     # prefix is not used on ARM Mac (SDK paths passed via -isysroot instead)
+     # prefix = ""
+     includes = []
```

---

## 8.3 CMake: `target_compile_options` instead of deprecated `COMPILE_FLAGS`

`[8rc3-to-8rc5]`

The `COMPILE_FLAGS` target property (used previously to inject `-fpermissive`, `-fvisibility=hidden`, etc.) is deprecated in modern CMake and was silently ignored — compile flags from section 7.2 (including `-Wno-deprecated-declarations`) never reached the compiler.

**pywrap/bindgen/CMakeLists.j2** and **templates/CMakeLists.j2** (project-level override; `ocp.toml` sets `template_path = "./templates"` so this file takes precedence)

```diff
  else()
    set_target_properties( {{ name }}
                           PROPERTIES
-                          CMAKE_CXX_FLAGS_RELEASE "-O3 "
-                          COMPILE_FLAGS "-fpermissive -fvisibility=hidden -fvisibility-inlines-hidden -Wno-deprecated-declarations" )
+                          CMAKE_CXX_FLAGS_RELEASE "-O3 " )
+   target_compile_options( {{ name }} PRIVATE
+                           -fpermissive -fvisibility=hidden -fvisibility-inlines-hidden
+                           -Wno-deprecated-declarations )
  endif()
```

Known residual issue: Apple Clang 21 does not honor `-Wno-deprecated-declarations` for `__attribute__((deprecated))` attributes on overloaded function addresses, so ~200 deprecation warnings remain. This is a compiler bug (or deliberate restriction) — confirmed via minimal standalone reproducer — not a pywrap issue.

---
