# Modifications to This Fork

This repository is a modified fork of Tabbycat, licensed under the GNU Affero General Public License v3.0.

- Upstream project: https://github.com/TabbycatDebate/tabbycat
- This fork: https://github.com/sebastian-grof/tabbycat
- Maintainer: Sebastian Grof

## Fork Notice

This fork contains local modifications for SDA tournament operations and hosting.

As of 2026-06-15, the fork includes changes in areas such as:

- draw generation and bye-team selection, including solo elimination draws
- side-allocation behavior and UI, including opposite-of-round handling
- archive export/import for byes and forfeits
- changes in vote distribution behavior
- cross-examination support
- global Breaks/qualification tools for SDA seasonal qualification tracking, including regional rankings, region visibility controls, configurable N-1 ranking, and per-season identity management
- UI and export changes in ballots, including private-URL ballots with editable text feedback
- DebateXML / results converter site tool for exchanging data with external SDA systems
- tournament-specific workflow and deployment adjustments
- footer source-code link for hosted instances
- feedback and adjudicator-stats export to an external database (DR) through the API
- Support for SDA 1-speech format (JDL)
- Slovak localisation additions and fixes (side names, ballots, JDL export, browser gettext catalogs)

## Source Code for Hosted Version

If you are using or interacting with a hosted instance of this fork, the corresponding source code for that deployed version is intended to be available from:

- https://github.com/sebastian-grof/tabbycat

## Licensing

This fork remains distributed under the GNU Affero General Public License v3.0.
See [LICENSE.md](LICENSE.md) for the full license text.
