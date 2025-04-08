from pathlib import Path

VALID_FILE_PATTERN = "**/**.py"
ZIP_FILE_NAME = "code.zip"


cwd = Path.cwd()
home_dir = Path.home()
aws_dir = home_dir / ".aws"
