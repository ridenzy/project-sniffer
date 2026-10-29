from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from project_sniffer.reading import (
    FileReadResult,
)


class SourceLanguage(str, Enum):
    """
    Semantic source-language identity.

    Recognition does not imply that Project Sniffer currently has a parser
    or analyzer for the language.
    """

    ABAP = "abap"
    ADA = "ada"
    ASSEMBLY = "assembly"
    BASIC = "basic"
    BATCH = "batch"
    BLADE = "blade"

    C = "c"
    CAIRO = "cairo"
    CLOJURE = "clojure"
    CMAKE = "cmake"
    COBOL = "cobol"
    CPP = "cpp"
    CSHARP = "csharp"
    CSS = "css"
    CUE = "cue"
    CYPHER = "cypher"

    D = "d"
    DART = "dart"
    DHALL = "dhall"
    DOCKERFILE = "dockerfile"

    EJS = "ejs"
    ELIXIR = "elixir"
    ELM = "elm"
    ERB = "erb"
    ERLANG = "erlang"

    FISH = "fish"
    FORTRAN = "fortran"
    FSHARP = "fsharp"

    GLEAM = "gleam"
    GLSL = "glsl"
    GO = "go"
    GRAPHQL = "graphql"
    GROOVY = "groovy"

    HANDLEBARS = "handlebars"
    HASKELL = "haskell"
    HCL = "hcl"
    HLSL = "hlsl"
    HTML = "html"

    INI = "ini"

    JAVA = "java"
    JAVASCRIPT = "javascript"
    JINJA = "jinja"
    JSON = "json"
    JSONNET = "jsonnet"
    JULIA = "julia"

    KOTLIN = "kotlin"

    LATEX = "latex"
    LESS = "less"
    LUA = "lua"

    MAKEFILE = "makefile"
    MARKDOWN = "markdown"
    MATLAB = "matlab"
    MESON = "meson"
    MOVE = "move"

    NIM = "nim"
    NIX = "nix"
    NUSHELL = "nushell"

    OBJECTIVE_C = "objective_c"
    OBJECTIVE_CPP = "objective_cpp"
    OCAML = "ocaml"

    PASCAL = "pascal"
    PERL = "perl"
    PHP = "php"
    PLAIN_TEXT = "plain_text"
    PLPGSQL = "plpgsql"
    PLSQL = "plsql"
    POWERSHELL = "powershell"
    PRISMA = "prisma"
    PROTOBUF = "protobuf"
    PUG = "pug"
    PYTHON = "python"

    R = "r"
    RESTRUCTURED_TEXT = "restructured_text"
    RUBY = "ruby"
    RUST = "rust"

    SASS = "sass"
    SAS = "sas"
    SCALA = "scala"
    SCSS = "scss"
    SHELL = "shell"
    SOLIDITY = "solidity"
    SPARQL = "sparql"
    SQL = "sql"
    STARLARK = "starlark"
    STATA = "stata"
    SVELTE = "svelte"
    SWIFT = "swift"
    SYSTEMVERILOG = "systemverilog"

    TCL = "tcl"
    THRIFT = "thrift"
    TOML = "toml"
    TSQL = "tsql"
    TWIG = "twig"
    TYPESCRIPT = "typescript"

    VERILOG = "verilog"
    VHDL = "vhdl"
    VISUAL_BASIC = "visual_basic"
    VUE = "vue"
    VYPER = "vyper"

    WGSL = "wgsl"

    XML = "xml"

    YAML = "yaml"

    ZIG = "zig"

    UNKNOWN = "unknown"

    @property
    def markdown_fence_label(
        self,
    ) -> str:
        """
        Return a suitable Markdown code-fence information string.

        This affects report presentation only. It is not parser capability.
        """

        if self is SourceLanguage.ASSEMBLY:
            return "asm"

        if self is SourceLanguage.SHELL:
            return "bash"

        if self is SourceLanguage.CSHARP:
            return "cs"

        if self is SourceLanguage.OBJECTIVE_C:
            return "objective-c"

        if self is SourceLanguage.OBJECTIVE_CPP:
            return "objective-cpp"

        if self is SourceLanguage.PLPGSQL:
            return "pgsql"

        if self is SourceLanguage.RESTRUCTURED_TEXT:
            return "rst"

        if self is SourceLanguage.VISUAL_BASIC:
            return "vbnet"

        if self in {
            SourceLanguage.PLAIN_TEXT,
            SourceLanguage.UNKNOWN,
        }:
            return "text"

        return self.value


@dataclass(frozen=True)
class SourceEvidence:
    """
    Shared source metadata built from one existing safe-read result.

    The read result is retained by reference. Source content is not copied
    or reopened by this evidence layer.
    """

    read_result: FileReadResult
    language: SourceLanguage