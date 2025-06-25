# Library Consolidation Proposal

This document outlines a path for simplifying the current layout of the
`lib` directory.  Today we maintain a Perl module (`Acme::Frobnitz`) and a
set of standalone Python files in `python_utils`.  The mixed language
approach and many entry points make the codebase harder to maintain.

## Goals

* Provide a single, cohesive Python package for all internal utilities.
* Remove duplication between scripts and libraries.
* Reduce the cross-language maintenance burden.
* Make command line entry points easier to discover.

## Proposed Structure

```
lib/
    mimesis/
        __init__.py
        downloader.py
        video.py
        tasks.py
        whisper.py
        ...
```

*The existing `python_utils` modules become submodules of `mimesis`.*
All scripts in `bin/` would import from this package instead of relying on
loose files on the path.

We also suggest rewriting the Perl wrapper (`Acme::Frobnitz`) in Python so
that all tooling lives in one language.  Any features unique to the Perl
module can be ported into a Python helper class inside the new package.

## Steps

1. Create `lib/mimesis` and move the contents of `lib/python_utils` into it,
   updating the imports accordingly.
2. Convert the functions from `Acme::Frobnitz` to Python.  This removes the
   dependency on Perl while keeping the same functionality.
3. Update the scripts under `bin/` to use the `mimesis` package.
4. Provide a top‑level console script (e.g. `mimesis-cli`) that exposes the
   common operations from a single command.

This consolidation keeps the repository small and approachable while making
future development easier.
