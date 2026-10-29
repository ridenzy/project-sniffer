from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from project_sniffer.evidence.models import (
    SourceLanguage,
)


@dataclass(frozen=True)
class LanguageDefinition:
    """
    Path-recognition metadata for one SourceLanguage.

    Empty suffix/basename collections mean that the language is represented
    by the model but currently requires a future content/heuristic detector.
    """

    language: SourceLanguage
    display_name: str
    category: str
    suffixes: tuple[str, ...] = ()
    exact_suffixes: tuple[str, ...] = ()
    basenames: tuple[str, ...] = ()
    note: str = ""

    @property
    def path_recognized(
        self,
    ) -> bool:
        return bool(
            self.suffixes
            or self.exact_suffixes
            or self.basenames
        )


def _definition(
    language: SourceLanguage,
    display_name: str,
    category: str,
    *,
    suffixes: tuple[str, ...] = (),
    exact_suffixes: tuple[str, ...] = (),
    basenames: tuple[str, ...] = (),
    note: str = "",
) -> LanguageDefinition:
    return LanguageDefinition(
        language=language,
        display_name=display_name,
        category=category,
        suffixes=suffixes,
        exact_suffixes=exact_suffixes,
        basenames=basenames,
        note=note,
    )


LANGUAGE_DEFINITIONS = (
    _definition(
        SourceLanguage.ABAP,
        "ABAP",
        "programming",
        suffixes=(".abap",),
    ),
    _definition(
        SourceLanguage.ADA,
        "Ada",
        "programming",
        suffixes=(".adb", ".ada", ".ads"),
    ),
    _definition(
        SourceLanguage.ASSEMBLY,
        "Assembly",
        "programming",
        suffixes=(".asm", ".nasm"),
    ),
    _definition(
        SourceLanguage.BASIC,
        "BASIC",
        "programming",
        suffixes=(".bas", ".basic"),
    ),
    _definition(
        SourceLanguage.BATCH,
        "Windows Batch",
        "scripting",
        suffixes=(".bat", ".cmd"),
    ),
    _definition(
        SourceLanguage.BLADE,
        "Blade",
        "template",
        suffixes=(".blade.php",),
    ),
    _definition(
        SourceLanguage.C,
        "C",
        "programming",
        suffixes=(".c",),
        note=".h remains ambiguous and is not path-classified.",
    ),
    _definition(
        SourceLanguage.CAIRO,
        "Cairo",
        "smart-contract",
        suffixes=(".cairo",),
    ),
    _definition(
        SourceLanguage.CLOJURE,
        "Clojure",
        "programming",
        suffixes=(".clj", ".cljs", ".cljc"),
    ),
    _definition(
        SourceLanguage.CMAKE,
        "CMake",
        "build",
        suffixes=(".cmake",),
        basenames=("CMakeLists.txt",),
    ),
    _definition(
        SourceLanguage.COBOL,
        "COBOL",
        "programming",
        suffixes=(".cob", ".cbl", ".cobol"),
    ),
    _definition(
        SourceLanguage.CPP,
        "C++",
        "programming",
        suffixes=(
            ".cc",
            ".cp",
            ".cpp",
            ".cxx",
            ".c++",
            ".hh",
            ".hpp",
            ".hxx",
            ".h++",
            ".inl",
            ".ipp",
            ".tcc",
            ".tpp",
        ),
        exact_suffixes=(".C",),
        note=".h remains ambiguous with C and related languages.",
    ),
    _definition(
        SourceLanguage.CSHARP,
        "C#",
        "programming",
        suffixes=(".cs", ".csx"),
    ),
    _definition(
        SourceLanguage.CSS,
        "CSS",
        "stylesheet",
        suffixes=(".css",),
    ),
    _definition(
        SourceLanguage.CUE,
        "CUE",
        "configuration",
        suffixes=(".cue",),
    ),
    _definition(
        SourceLanguage.CYPHER,
        "Cypher",
        "database",
        suffixes=(".cypher",),
    ),
    _definition(
        SourceLanguage.D,
        "D",
        "programming",
        suffixes=(".d",),
    ),
    _definition(
        SourceLanguage.DART,
        "Dart",
        "programming",
        suffixes=(".dart",),
    ),
    _definition(
        SourceLanguage.DHALL,
        "Dhall",
        "configuration",
        suffixes=(".dhall",),
    ),
    _definition(
        SourceLanguage.DOCKERFILE,
        "Dockerfile",
        "build",
        basenames=("Dockerfile", "Containerfile"),
    ),
    _definition(
        SourceLanguage.EJS,
        "EJS",
        "template",
        suffixes=(".ejs",),
    ),
    _definition(
        SourceLanguage.ELIXIR,
        "Elixir",
        "programming",
        suffixes=(".ex", ".exs"),
    ),
    _definition(
        SourceLanguage.ELM,
        "Elm",
        "programming",
        suffixes=(".elm",),
    ),
    _definition(
        SourceLanguage.ERB,
        "ERB",
        "template",
        suffixes=(".erb",),
    ),
    _definition(
        SourceLanguage.ERLANG,
        "Erlang",
        "programming",
        suffixes=(".erl", ".hrl"),
    ),
    _definition(
        SourceLanguage.FISH,
        "Fish",
        "scripting",
        suffixes=(".fish",),
    ),
    _definition(
        SourceLanguage.FORTRAN,
        "Fortran",
        "programming",
        suffixes=(
            ".f",
            ".for",
            ".f77",
            ".f90",
            ".f95",
            ".f03",
            ".f08",
            ".fpp",
        ),
    ),
    _definition(
        SourceLanguage.FSHARP,
        "F#",
        "programming",
        suffixes=(".fs", ".fsi", ".fsx"),
    ),
    _definition(
        SourceLanguage.GLEAM,
        "Gleam",
        "programming",
        suffixes=(".gleam",),
    ),
    _definition(
        SourceLanguage.GLSL,
        "GLSL",
        "shader",
        suffixes=(
            ".glsl",
            ".vert",
            ".frag",
            ".geom",
            ".tesc",
            ".tese",
            ".comp",
        ),
    ),
    _definition(
        SourceLanguage.GO,
        "Go",
        "programming",
        suffixes=(".go",),
    ),
    _definition(
        SourceLanguage.GRAPHQL,
        "GraphQL",
        "schema-query",
        suffixes=(".graphql", ".gql"),
    ),
    _definition(
        SourceLanguage.GROOVY,
        "Groovy",
        "programming",
        suffixes=(".groovy", ".gvy", ".gy", ".gsh"),
    ),
    _definition(
        SourceLanguage.HANDLEBARS,
        "Handlebars",
        "template",
        suffixes=(".hbs", ".handlebars"),
    ),
    _definition(
        SourceLanguage.HASKELL,
        "Haskell",
        "programming",
        suffixes=(".hs", ".lhs"),
    ),
    _definition(
        SourceLanguage.HCL,
        "HCL / Terraform",
        "infrastructure",
        suffixes=(".hcl", ".tf", ".tfvars"),
    ),
    _definition(
        SourceLanguage.HLSL,
        "HLSL",
        "shader",
        suffixes=(".hlsl", ".fx", ".fxh"),
    ),
    _definition(
        SourceLanguage.HTML,
        "HTML",
        "markup",
        suffixes=(".html", ".htm"),
    ),
    _definition(
        SourceLanguage.INI,
        "INI / EditorConfig",
        "configuration",
        suffixes=(".ini",),
        basenames=(".editorconfig",),
    ),
    _definition(
        SourceLanguage.JAVA,
        "Java",
        "programming",
        suffixes=(".java",),
    ),
    _definition(
        SourceLanguage.JAVASCRIPT,
        "JavaScript",
        "programming",
        suffixes=(".js", ".jsx", ".mjs", ".cjs"),
    ),
    _definition(
        SourceLanguage.JINJA,
        "Jinja",
        "template",
        suffixes=(".jinja", ".jinja2", ".j2"),
    ),
    _definition(
        SourceLanguage.JSON,
        "JSON",
        "data",
        suffixes=(".json",),
    ),
    _definition(
        SourceLanguage.JSONNET,
        "Jsonnet",
        "configuration",
        suffixes=(".jsonnet", ".libsonnet"),
    ),
    _definition(
        SourceLanguage.JULIA,
        "Julia",
        "programming",
        suffixes=(".jl",),
    ),
    _definition(
        SourceLanguage.KOTLIN,
        "Kotlin",
        "programming",
        suffixes=(".kt", ".kts"),
    ),
    _definition(
        SourceLanguage.LATEX,
        "LaTeX",
        "documentation",
        suffixes=(".tex",),
    ),
    _definition(
        SourceLanguage.LESS,
        "Less",
        "stylesheet",
        suffixes=(".less",),
    ),
    _definition(
        SourceLanguage.LUA,
        "Lua",
        "scripting",
        suffixes=(".lua",),
    ),
    _definition(
        SourceLanguage.MAKEFILE,
        "Makefile",
        "build",
        basenames=("Makefile", "GNUmakefile"),
    ),
    _definition(
        SourceLanguage.MARKDOWN,
        "Markdown",
        "documentation",
        suffixes=(".md", ".markdown"),
    ),
    _definition(
        SourceLanguage.MATLAB,
        "MATLAB",
        "programming",
        note=(
            ".m is deliberately unresolved because Objective-C and other "
            "languages also use it."
        ),
    ),
    _definition(
        SourceLanguage.MESON,
        "Meson",
        "build",
        basenames=("meson.build", "meson_options.txt"),
    ),
    _definition(
        SourceLanguage.MOVE,
        "Move",
        "smart-contract",
        suffixes=(".move",),
    ),
    _definition(
        SourceLanguage.NIM,
        "Nim",
        "programming",
        suffixes=(".nim",),
    ),
    _definition(
        SourceLanguage.NIX,
        "Nix",
        "infrastructure",
        suffixes=(".nix",),
    ),
    _definition(
        SourceLanguage.NUSHELL,
        "Nushell",
        "scripting",
        suffixes=(".nu",),
    ),
    _definition(
        SourceLanguage.OBJECTIVE_C,
        "Objective-C",
        "programming",
        note=(
            ".m is deliberately unresolved because MATLAB and other "
            "languages also use it."
        ),
    ),
    _definition(
        SourceLanguage.OBJECTIVE_CPP,
        "Objective-C++",
        "programming",
        suffixes=(".mm",),
    ),
    _definition(
        SourceLanguage.OCAML,
        "OCaml",
        "programming",
        suffixes=(".ml", ".mli"),
    ),
    _definition(
        SourceLanguage.PASCAL,
        "Pascal",
        "programming",
        suffixes=(".pas", ".pascal", ".pp"),
    ),
    _definition(
        SourceLanguage.PERL,
        "Perl",
        "scripting",
        suffixes=(".perl",),
        note=(
            ".pl and .pm are deliberately excluded from deterministic "
            "path-only recognition because they are shared by other "
            "language ecosystems."
        ),
    ),
    _definition(
        SourceLanguage.PHP,
        "PHP",
        "programming",
        suffixes=(".php", ".phtml"),
    ),
    _definition(
        SourceLanguage.PLAIN_TEXT,
        "Plain text",
        "text",
        suffixes=(".txt",),
        basenames=(".gitignore", "DCO", "LICENSE"),
    ),
    _definition(
        SourceLanguage.PLPGSQL,
        "PL/pgSQL",
        "database",
        suffixes=(".pgsql",),
        note=(
            "Generic .sql remains SQL until stronger PostgreSQL-dialect "
            "evidence exists."
        ),
    ),
    _definition(
        SourceLanguage.PLSQL,
        "PL/SQL",
        "database",
        suffixes=(".pls", ".plsql"),
        note="Generic .sql remains SQL because the dialect is ambiguous.",
    ),
    _definition(
        SourceLanguage.POWERSHELL,
        "PowerShell",
        "scripting",
        suffixes=(".ps1", ".psm1", ".psd1"),
    ),
    _definition(
        SourceLanguage.PRISMA,
        "Prisma Schema",
        "schema-query",
        suffixes=(".prisma",),
    ),
    _definition(
        SourceLanguage.PROTOBUF,
        "Protocol Buffers",
        "schema-query",
        suffixes=(".proto",),
    ),
    _definition(
        SourceLanguage.PUG,
        "Pug",
        "template",
        suffixes=(".pug", ".jade"),
    ),
    _definition(
        SourceLanguage.PYTHON,
        "Python",
        "programming",
        suffixes=(".py", ".pyi"),
    ),
    _definition(
        SourceLanguage.R,
        "R",
        "programming",
        suffixes=(".r",),
    ),
    _definition(
        SourceLanguage.RESTRUCTURED_TEXT,
        "reStructuredText",
        "documentation",
        suffixes=(".rst",),
    ),
    _definition(
        SourceLanguage.RUBY,
        "Ruby",
        "programming",
        suffixes=(".rb",),
        basenames=("Gemfile", "Rakefile"),
    ),
    _definition(
        SourceLanguage.RUST,
        "Rust",
        "programming",
        suffixes=(".rs",),
    ),
    _definition(
        SourceLanguage.SASS,
        "Sass",
        "stylesheet",
        suffixes=(".sass",),
    ),
    _definition(
        SourceLanguage.SAS,
        "SAS",
        "programming",
        suffixes=(".sas",),
    ),
    _definition(
        SourceLanguage.SCALA,
        "Scala",
        "programming",
        suffixes=(".scala", ".sc"),
    ),
    _definition(
        SourceLanguage.SCSS,
        "SCSS",
        "stylesheet",
        suffixes=(".scss",),
    ),
    _definition(
        SourceLanguage.SHELL,
        "Shell",
        "scripting",
        suffixes=(".sh", ".bash", ".zsh"),
        basenames=(".bashrc", ".zshrc"),
    ),
    _definition(
        SourceLanguage.SOLIDITY,
        "Solidity",
        "smart-contract",
        note=(
            ".sol is deliberately unresolved by path alone because other "
            "formats also use the extension."
        ),
    ),
    _definition(
        SourceLanguage.SPARQL,
        "SPARQL",
        "schema-query",
        suffixes=(".rq", ".sparql"),
    ),
    _definition(
        SourceLanguage.SQL,
        "SQL",
        "database",
        suffixes=(".sql",),
    ),
    _definition(
        SourceLanguage.STARLARK,
        "Starlark / Bazel",
        "build",
        suffixes=(".bzl",),
        basenames=(
            "BUILD",
            "BUILD.bazel",
            "WORKSPACE",
            "WORKSPACE.bazel",
        ),
    ),
    _definition(
        SourceLanguage.STATA,
        "Stata",
        "programming",
        suffixes=(".do", ".ado"),
    ),
    _definition(
        SourceLanguage.SVELTE,
        "Svelte",
        "markup",
        suffixes=(".svelte",),
    ),
    _definition(
        SourceLanguage.SWIFT,
        "Swift",
        "programming",
        suffixes=(".swift",),
    ),
    _definition(
        SourceLanguage.SYSTEMVERILOG,
        "SystemVerilog",
        "hardware",
        suffixes=(".sv", ".svh"),
    ),
    _definition(
        SourceLanguage.TCL,
        "Tcl",
        "scripting",
        suffixes=(".tcl",),
    ),
    _definition(
        SourceLanguage.THRIFT,
        "Thrift",
        "schema-query",
        suffixes=(".thrift",),
    ),
    _definition(
        SourceLanguage.TOML,
        "TOML",
        "configuration",
        suffixes=(".toml",),
    ),
    _definition(
        SourceLanguage.TSQL,
        "T-SQL",
        "database",
        note=(
            "Generic .sql is deliberately left as SQL until dialect "
            "evidence exists."
        ),
    ),
    _definition(
        SourceLanguage.TWIG,
        "Twig",
        "template",
        suffixes=(".twig",),
    ),
    _definition(
        SourceLanguage.TYPESCRIPT,
        "TypeScript",
        "programming",
        suffixes=(
            ".d.ts",
            ".ts",
            ".tsx",
            ".mts",
            ".cts",
        ),
    ),
    _definition(
        SourceLanguage.VERILOG,
        "Verilog",
        "hardware",
        note=(
            ".v is deliberately unresolved because it is shared with "
            "other source formats."
        ),
    ),
    _definition(
        SourceLanguage.VHDL,
        "VHDL",
        "hardware",
        suffixes=(".vhd", ".vhdl"),
    ),
    _definition(
        SourceLanguage.VISUAL_BASIC,
        "Visual Basic .NET",
        "programming",
        suffixes=(".vb",),
    ),
    _definition(
        SourceLanguage.VUE,
        "Vue",
        "markup",
        suffixes=(".vue",),
    ),
    _definition(
        SourceLanguage.VYPER,
        "Vyper",
        "smart-contract",
        suffixes=(".vy",),
    ),
    _definition(
        SourceLanguage.WGSL,
        "WGSL",
        "shader",
        suffixes=(".wgsl",),
    ),
    _definition(
        SourceLanguage.XML,
        "XML",
        "data",
        suffixes=(".xml",),
    ),
    _definition(
        SourceLanguage.YAML,
        "YAML",
        "configuration",
        suffixes=(".yaml", ".yml"),
    ),
    _definition(
        SourceLanguage.ZIG,
        "Zig",
        "programming",
        suffixes=(".zig",),
    ),
    _definition(
        SourceLanguage.UNKNOWN,
        "Unknown",
        "unknown",
        note="No deterministic language evidence was available.",
    ),
)


_DEFINITION_BY_LANGUAGE = {
    definition.language: definition
    for definition in LANGUAGE_DEFINITIONS
}


def _build_indexes() -> tuple[
    dict[str, SourceLanguage],
    tuple[tuple[str, SourceLanguage], ...],
    tuple[tuple[str, SourceLanguage], ...],
]:
    basename_index: dict[str, SourceLanguage] = {}
    folded_suffix_index: dict[str, SourceLanguage] = {}
    exact_suffix_index: dict[str, SourceLanguage] = {}

    for definition in LANGUAGE_DEFINITIONS:
        for basename in definition.basenames:
            key = basename.casefold()

            existing = basename_index.get(
                key
            )

            if (
                existing is not None
                and existing is not definition.language
            ):
                raise RuntimeError(
                    "duplicate language basename rule: "
                    f"{basename}"
                )

            basename_index[key] = (
                definition.language
            )

        for suffix in definition.suffixes:
            key = suffix.casefold()

            existing = folded_suffix_index.get(
                key
            )

            if (
                existing is not None
                and existing is not definition.language
            ):
                raise RuntimeError(
                    "duplicate language suffix rule: "
                    f"{suffix}"
                )

            folded_suffix_index[key] = (
                definition.language
            )

        for suffix in definition.exact_suffixes:
            existing = exact_suffix_index.get(
                suffix
            )

            if (
                existing is not None
                and existing is not definition.language
            ):
                raise RuntimeError(
                    "duplicate exact language suffix rule: "
                    f"{suffix}"
                )

            exact_suffix_index[suffix] = (
                definition.language
            )

    folded_suffix_rules = tuple(
        sorted(
            folded_suffix_index.items(),
            key=lambda item: len(
                item[0]
            ),
            reverse=True,
        )
    )

    exact_suffix_rules = tuple(
        sorted(
            exact_suffix_index.items(),
            key=lambda item: len(
                item[0]
            ),
            reverse=True,
        )
    )

    return (
        basename_index,
        folded_suffix_rules,
        exact_suffix_rules,
    )


(
    _BASENAME_INDEX,
    _FOLDED_SUFFIX_RULES,
    _EXACT_SUFFIX_RULES,
) = _build_indexes()


def get_language_definition(
    language: SourceLanguage,
) -> LanguageDefinition:
    return _DEFINITION_BY_LANGUAGE[
        language
    ]


def classify_path_language(
    relative_path: str,
) -> SourceLanguage:
    """
    Classify a path using deterministic path evidence only.

    Exact case-sensitive suffix rules are checked before case-insensitive
    suffixes. Compound suffixes are matched longest-first.
    """

    normalized = relative_path.replace(
        "\\",
        "/",
    )

    path = PurePosixPath(
        normalized
    )

    filename = path.name

    basename_language = (
        _BASENAME_INDEX.get(
            filename.casefold()
        )
    )

    if basename_language is not None:
        return basename_language

    for suffix, language in (
        _EXACT_SUFFIX_RULES
    ):
        if filename.endswith(
            suffix
        ):
            return language

    folded_filename = filename.casefold()

    for suffix, language in (
        _FOLDED_SUFFIX_RULES
    ):
        if folded_filename.endswith(
            suffix
        ):
            return language

    return SourceLanguage.UNKNOWN
