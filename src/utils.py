import zipfile
from pathlib import Path

from .defaults import cwd


def list_matching_files(pattern, skip_current_file=True):
    """
    List all files matching the given glob pattern in the current working directory,
    optionally skipping the current script file.

    Args:
        pattern (str): The glob pattern to match files against.
                      Example patterns: "*.txt", "data_*.csv", "log_[0-9]*.log"
        skip_current_file (bool): Whether to skip the current script file in the results.
                                 Defaults to True.

    Returns:
        list: A list of Path objects.
    """
    matching_files = []

    # Get the current script path if needed
    this_file = Path(__file__) if skip_current_file else None

    for p in cwd.glob(pattern):
        # Skip the current file if requested
        if skip_current_file and p == this_file:
            continue

        # Add the relative path to the results
        matching_files.append(p)

    return matching_files


def create_zip_from_paths(output_zip_path, file_paths, base_dir=None):
    """
    Create a zip file from a list of Path objects

    Args:
        output_zip_path: Path where the zip file will be saved
        file_paths: List of Path objects representing files to be zipped
        base_dir: Optional Path object to use as the base directory for relative paths.
                  If None, uses current working directory
    """
    # Ensure output path is a Path object
    output_zip_path = Path(output_zip_path)

    # If no base_dir provided, use current working directory
    base_dir = Path(base_dir) if base_dir is not None else cwd

    # Create a new zip file with 'w' (write) mode
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add each file to the zip
        for file_path in file_paths:
            # Check if the file exists
            if file_path.is_file():
                # Calculate relative path for arcname
                try:
                    relative_path = file_path.relative_to(base_dir)
                    zipf.write(file_path, arcname=str(relative_path))

                except ValueError:
                    print(
                        f"Warning: {file_path} is not relative to {base_dir}, using filename only"
                    )
                    # If file is not relative to base_dir, just use the filename
                    zipf.write(file_path, arcname=file_path.name)
            else:
                print(f"Warning: {file_path} is not a file or doesn't exist")

    return output_zip_path


def safe_input(prompt, cannot_be_empty=True):
    while True:
        try:
            value = input(prompt).strip()

            if not value and cannot_be_empty:
                print("It cannot be empty...")

            return value
        except KeyboardInterrupt:
            exit(0)


def human_readable_size(size_bytes):
    """
    Convert a size in bytes to a human-readable string.

    Args:
        size_bytes (int): Size in bytes

    Returns:
        str: Human-readable size string (e.g., "2.5 KB", "1.2 MB")
    """
    KB = 1024
    MB = KB * 1024

    unit = ""
    size = 0

    if size_bytes < KB:
        unit = "bytes"
        size = size_bytes

    elif size_bytes < MB:
        unit = "KB"
        size = size_bytes / KB

    else:
        unit = "MB"
        size = size_bytes / MB

    size = f"{size:.1f}".rstrip("0").rstrip(".")

    return f"{size.ljust(4)} {unit.ljust(5)}"


def list_zip_contents(zip_path):
    """
    Get information about all files contained within a ZIP archive.

    Args:
        zip_path (str or Path): Path to the ZIP file

    Returns:
        list: A list of ZipInfo objects for each file in the ZIP
    """

    zip_path = Path(zip_path)
    if not zip_path.exists():
        return []

    with zipfile.ZipFile(zip_path, "r") as zipf:
        return zipf.infolist()
