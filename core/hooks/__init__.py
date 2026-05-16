"""core/hooks package — adapter hook implementations.

Hooks are kept here (not in core/cli.py) so the per-harness wire format is
isolated from the user-facing CLI surface. Each module exposes pure helpers
that the corresponding ``paperboard <subcommand>`` entry point orchestrates.
"""
