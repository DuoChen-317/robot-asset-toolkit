"""Shared placement of process artifacts outside final asset directories."""
from pathlib import Path


def resolve_work_dir(final_directory, explicit=None):
    final_directory = Path(final_directory).expanduser().resolve()
    work = (Path(explicit) if explicit is not None else final_directory.parent / '_conversion_work').expanduser().resolve()
    if work == final_directory or work.is_relative_to(final_directory):
        raise ValueError('Work directory must be outside the final asset directory')
    return work
