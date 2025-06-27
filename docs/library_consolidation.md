# Library Consolidation Proposal

This document outlines a path for simplifying the current layout of the
`lib` directory.  Historically we maintained a Perl module (`Acme::Frobnitz`)
and a set of standalone Python files under `python_utils`.  The mixed language
approach and many entry points made the codebase harder to maintain.  The
Python modules now live directly in `lib/`.

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

The standalone utilities once found in `python_utils` now live directly under
`lib/` as part of the growing `mimesis` package.  All scripts in `bin/`
import from this location instead of relying on loose files on the path.

We replaced the old Perl wrapper (`Acme::Frobnitz`) with a Python
implementation so that all tooling now lives in one language.  Any
remaining features from the Perl module have been ported into helper
classes inside the package.

## Steps

1. Move the helper modules from `lib/python_utils` into `lib/`, updating the
   imports accordingly.
2. Convert the functions from `Acme::Frobnitz` to Python.  This removed the
   dependency on Perl while keeping the same functionality.
3. Update the scripts under `bin/` to use the `mimesis` package.
4. Provide a top‑level console script (e.g. `mimesis-cli`) that exposes the
   common operations from a single command.

This consolidation keeps the repository small and approachable while making
future development easier.
