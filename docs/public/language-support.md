# Project Sniffer Language Support

## Purpose

This document records the source-language identities currently represented by
Project Sniffer and distinguishes path recognition from actual parser support.

A language being listed here does not mean that Project Sniffer can already
parse its syntax or trace calls, imports, routes, database usage, or other
semantic relationships.

The capability levels are:

1. **Registered** — the language has a `SourceLanguage` identity.
2. **Path-recognized** — deterministic filename/suffix evidence can identify it.
3. **Parsed** — a real parser can produce normalized semantic evidence.
4. **Analyzer-supported** — analyzers consume that parsed evidence.

Phase 2F-A implements levels 1 and 2. Phase 2F-B now provides level 3 for
Python while the remaining registered languages are still recognition-only.

Phase 2F-C now provides level-4 analyzer support for confirmed internal Python
import dependencies through the initial `--trace` analyzer.

## Recognition policy

Project Sniffer prefers `UNKNOWN` over a confidently wrong classification.

Ambiguous extensions are therefore not assigned solely from their suffix.
Examples currently include `.h`, `.m`, `.pl`, `.sol`, and `.v`.

Generic `.sql` is classified as SQL. PostgreSQL PL/pgSQL is recognized from
stronger path evidence such as `.pgsql`; database-dialect inference is a
separate future concern.

## Current registry

| Registry ID | Language / syntax | Category | Path recognition | Fence | Notes |
| --- | --- | --- | --- | --- | --- |
| `abap` | ABAP | programming | Yes | `abap` |  |
| `ada` | Ada | programming | Yes | `ada` |  |
| `assembly` | Assembly | programming | Yes | `asm` |  |
| `basic` | BASIC | programming | Yes | `basic` |  |
| `batch` | Windows Batch | scripting | Yes | `batch` |  |
| `blade` | Blade | template | Yes | `blade` |  |
| `c` | C | programming | Yes | `c` | .h remains ambiguous and is not path-classified. |
| `cairo` | Cairo | smart-contract | Yes | `cairo` |  |
| `clojure` | Clojure | programming | Yes | `clojure` |  |
| `cmake` | CMake | build | Yes | `cmake` |  |
| `cobol` | COBOL | programming | Yes | `cobol` |  |
| `cpp` | C++ | programming | Yes | `cpp` | .h remains ambiguous with C and related languages. |
| `csharp` | C# | programming | Yes | `cs` | Recognizes `.cs` and `.csx`. |
| `css` | CSS | stylesheet | Yes | `css` |  |
| `cue` | CUE | configuration | Yes | `cue` |  |
| `cypher` | Cypher | database | Yes | `cypher` |  |
| `d` | D | programming | Yes | `d` |  |
| `dart` | Dart | programming | Yes | `dart` |  |
| `dhall` | Dhall | configuration | Yes | `dhall` |  |
| `dockerfile` | Dockerfile | build | Yes | `dockerfile` |  |
| `ejs` | EJS | template | Yes | `ejs` |  |
| `elixir` | Elixir | programming | Yes | `elixir` |  |
| `elm` | Elm | programming | Yes | `elm` |  |
| `erb` | ERB | template | Yes | `erb` |  |
| `erlang` | Erlang | programming | Yes | `erlang` |  |
| `fish` | Fish | scripting | Yes | `fish` |  |
| `fortran` | Fortran | programming | Yes | `fortran` |  |
| `fsharp` | F# | programming | Yes | `fsharp` |  |
| `gleam` | Gleam | programming | Yes | `gleam` |  |
| `glsl` | GLSL | shader | Yes | `glsl` |  |
| `go` | Go | programming | Yes | `go` |  |
| `graphql` | GraphQL | schema-query | Yes | `graphql` |  |
| `groovy` | Groovy | programming | Yes | `groovy` |  |
| `handlebars` | Handlebars | template | Yes | `handlebars` |  |
| `haskell` | Haskell | programming | Yes | `haskell` |  |
| `hcl` | HCL / Terraform | infrastructure | Yes | `hcl` |  |
| `hlsl` | HLSL | shader | Yes | `hlsl` |  |
| `html` | HTML | markup | Yes | `html` |  |
| `ini` | INI / EditorConfig | configuration | Yes | `ini` |  |
| `java` | Java | programming | Yes | `java` |  |
| `javascript` | JavaScript | programming | Yes | `javascript` |  |
| `jinja` | Jinja | template | Yes | `jinja` |  |
| `json` | JSON | data | Yes | `json` |  |
| `jsonnet` | Jsonnet | configuration | Yes | `jsonnet` |  |
| `julia` | Julia | programming | Yes | `julia` |  |
| `kotlin` | Kotlin | programming | Yes | `kotlin` |  |
| `latex` | LaTeX | documentation | Yes | `latex` |  |
| `less` | Less | stylesheet | Yes | `less` |  |
| `lua` | Lua | scripting | Yes | `lua` |  |
| `makefile` | Makefile | build | Yes | `makefile` |  |
| `markdown` | Markdown | documentation | Yes | `markdown` |  |
| `matlab` | MATLAB | programming | Registered only | `matlab` | .m is deliberately unresolved because Objective-C and other languages also use it. |
| `meson` | Meson | build | Yes | `meson` |  |
| `move` | Move | smart-contract | Yes | `move` |  |
| `nim` | Nim | programming | Yes | `nim` |  |
| `nix` | Nix | infrastructure | Yes | `nix` |  |
| `nushell` | Nushell | scripting | Yes | `nushell` |  |
| `objective_c` | Objective-C | programming | Registered only | `objective-c` | .m is deliberately unresolved because MATLAB and other languages also use it. |
| `objective_cpp` | Objective-C++ | programming | Yes | `objective-cpp` |  |
| `ocaml` | OCaml | programming | Yes | `ocaml` |  |
| `pascal` | Pascal | programming | Yes | `pascal` |  |
| `perl` | Perl | scripting | Yes | `perl` | .pl and .pm are deliberately excluded from deterministic path-only recognition because they are shared by other language ecosystems. |
| `php` | PHP | programming | Yes | `php` |  |
| `plain_text` | Plain text | text | Yes | `text` |  |
| `plpgsql` | PL/pgSQL | database | Yes | `pgsql` | Generic .sql remains SQL until stronger PostgreSQL-dialect evidence exists. |
| `plsql` | PL/SQL | database | Yes | `plsql` | Generic .sql remains SQL because the dialect is ambiguous. |
| `powershell` | PowerShell | scripting | Yes | `powershell` |  |
| `prisma` | Prisma Schema | schema-query | Yes | `prisma` |  |
| `protobuf` | Protocol Buffers | schema-query | Yes | `protobuf` |  |
| `pug` | Pug | template | Yes | `pug` |  |
| `python` | Python | programming | Yes | `python` |  |
| `r` | R | programming | Yes | `r` |  |
| `restructured_text` | reStructuredText | documentation | Yes | `rst` |  |
| `ruby` | Ruby | programming | Yes | `ruby` |  |
| `rust` | Rust | programming | Yes | `rust` |  |
| `sass` | Sass | stylesheet | Yes | `sass` |  |
| `sas` | SAS | programming | Yes | `sas` |  |
| `scala` | Scala | programming | Yes | `scala` |  |
| `scss` | SCSS | stylesheet | Yes | `scss` |  |
| `shell` | Shell | scripting | Yes | `bash` |  |
| `solidity` | Solidity | smart-contract | Registered only | `solidity` | .sol is deliberately unresolved by path alone because other formats also use the extension. |
| `sparql` | SPARQL | schema-query | Yes | `sparql` |  |
| `sql` | SQL | database | Yes | `sql` |  |
| `starlark` | Starlark / Bazel | build | Yes | `starlark` |  |
| `stata` | Stata | programming | Yes | `stata` |  |
| `svelte` | Svelte | markup | Yes | `svelte` |  |
| `swift` | Swift | programming | Yes | `swift` |  |
| `systemverilog` | SystemVerilog | hardware | Yes | `systemverilog` |  |
| `tcl` | Tcl | scripting | Yes | `tcl` |  |
| `thrift` | Thrift | schema-query | Yes | `thrift` |  |
| `toml` | TOML | configuration | Yes | `toml` |  |
| `tsql` | T-SQL | database | Registered only | `tsql` | Generic .sql is deliberately left as SQL until dialect evidence exists. |
| `twig` | Twig | template | Yes | `twig` |  |
| `typescript` | TypeScript | programming | Yes | `typescript` |  |
| `verilog` | Verilog | hardware | Registered only | `verilog` | .v is deliberately unresolved because it is shared with other source formats. |
| `vhdl` | VHDL | hardware | Yes | `vhdl` |  |
| `visual_basic` | Visual Basic .NET | programming | Yes | `vbnet` |  |
| `vue` | Vue | markup | Yes | `vue` |  |
| `vyper` | Vyper | smart-contract | Yes | `vyper` |  |
| `wgsl` | WGSL | shader | Yes | `wgsl` |  |
| `xml` | XML | data | Yes | `xml` |  |
| `yaml` | YAML | configuration | Yes | `yaml` |  |
| `zig` | Zig | programming | Yes | `zig` |  |
| `unknown` | Unknown | unknown | Registered only | `text` | No deterministic language evidence was available. |

The Python parser also records normalized call-site evidence. The initial
`--trace` analyzer currently consumes confirmed internal import dependencies;
call-target resolution and call-edge rendering remain the next trace stage.
Broader trace support for routes, APIs, file operations, exports, database
usage, and additional languages remains future work.

## Parser support

Parser support is tracked separately from path recognition.

| Registry ID | Parser ID | Status | Normalized evidence |
| --- | --- | --- | --- |
| `python` | `python-stdlib-ast` | Parsed | imports; classes; functions; async functions; call sites |

All other registered languages currently remain recognition-only. Python
parsing uses the standard-library AST and does not import or execute target
modules.

The initial `--trace` analyzer currently consumes confirmed internal Python
import dependencies. Python call sites are now normalized parser evidence, but
call-target resolution and call dependency edges are not implemented yet.
Broader trace support for routes, APIs, file operations, exports, database
usage, and additional languages remains future work.

## Future detection layers

Path recognition is intentionally only the first deterministic detector.
Later layers may include:

- shebang/interpreter detection;
- language-specific content heuristics;
- compound/framework file detection;
- SQL dialect detection;
- embedded-language detection;
- parser capability and parser-version reporting.
