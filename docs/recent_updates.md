# Recent Updates

This project continues to move entirely toward Python tooling.

## Removal of Frobnitz

We deleted the old Perl wrapper `Acme/Frobnitz.pm`. It previously
called into various Python scripts but made testing and packaging
harder. All features now live directly in the modules under `lib/`.

## Packaging cleanup

A new `MANIFEST.in` lists our scripts, configs and documentation so
that distribution packages include everything needed to run the
pipeline.
