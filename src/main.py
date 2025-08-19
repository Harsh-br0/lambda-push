import argparse
import tempfile
from pathlib import Path

from .aws_utils import setup_aws_credentials, update_lambda_function_code, validate_creds
from .defaults import DEFAULT_PROFILE, VALID_FILE_PATTERN, ZIP_FILE_NAME
from .utils import (
    create_zip_from_paths,
    human_readable_size,
    list_matching_files,
    list_zip_contents,
    safe_input,
)


def parse_arguments():
    """Parse command-line arguments for the lambda-push utility."""
    parser = argparse.ArgumentParser(
        prog="lambda-push",
        description="Quickly package and deploy Python files to AWS Lambda functions",
    )

    # argument for the function name
    parser.add_argument(
        "function_name", nargs="?", help="Name of the AWS Lambda function to update"
    )

    # Optional argument for include patterns, can be specified multiple times
    parser.add_argument(
        "-i",
        "--include",
        action="append",
        help="Glob pattern to include files (can be used multiple times). "
        "Example: --include '*.py' --include 'modules/**/*.py'",
    )

    # Dry run flag - create ZIP file without deploying
    parser.add_argument(
        "-d",
        "--dry",
        action="store_true",
        help="Dry run mode: create the ZIP file but don't deploy to Lambda",
    )

    parser.add_argument(
        "-p",
        "--profile",
        help="Pick creds from a different profile to deploy lambda function, "
        f"default: {DEFAULT_PROFILE}",
        default=DEFAULT_PROFILE,
        type=str.strip,
    )

    parser.add_argument(
        "--setup",
        action="store_true",
        help="Setup AWS Creds to deploy lambda function",
    )

    args = parser.parse_args()

    # Strip whitespace from function_name if it exists
    if args.function_name:
        args.function_name = args.function_name.strip()

    # Strip whitespace from include patterns if they exist
    if args.include:
        args.include = [pattern.strip() for pattern in args.include]

    if not (args.setup or args.function_name):
        parser.error("function_name is required unless --setup is specified")

    return args


def handle_setup():
    """Handle the AWS credentials setup and validation."""
    print("Setting up AWS credentials...")

    # Collect AWS credentials from user
    aws_access_key = safe_input("\nEnter AWS Access Key ID: ")
    aws_secret_key = safe_input("\nEnter AWS Secret Access Key: ")
    aws_region = safe_input("\nEnter AWS Region (e.g., us-east-1): ")

    # Basic validation
    if not aws_access_key or not aws_secret_key or not aws_region:
        print("Error: All credential fields are required.")
        return

    # Validate the credentials before saving
    print("\nValidating credentials...")
    session = validate_creds(
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region,
    )

    if session:
        # Save credentials only after successful validation
        print("\nSaving Credentials...")
        setup_aws_credentials(
            access_key=aws_access_key,
            secret_key=aws_secret_key,
            region=aws_region,
        )
        print("AWS credentials validated and saved successfully.")
    else:
        print("Failed to validate AWS credentials. Please check your input and try again.")


def print_zip_contents(zip_path):
    """
    Print the contents of a ZIP file with aligned size information.

    Args:
        zip_path (Path): Path to the ZIP file
    """

    zip_contents = list_zip_contents(zip_path)

    if not zip_contents:
        print("\nZIP file is empty or could not be read.")
        return

    # Find the longest filename for alignment
    max_name_length = 0

    for info in zip_contents:
        max_name_length = max(len(info.filename), max_name_length)

    max_name_length += 2  # keep some space between them

    total_size = 0
    print(f"\nContents of the ZIP file ({len(zip_contents)} files):")
    for info in zip_contents:
        size_str = human_readable_size(info.file_size)
        print(f"  - {info.filename.ljust(max_name_length)} ( {size_str} )")

        total_size += info.file_size

    # Print total size
    print(f"\n  Total size: {human_readable_size(total_size)}")


def main():
    # Parse command-line arguments
    args = parse_arguments()

    if args.setup:
        handle_setup()
        return

    operation_mode = "Packaging" if args.dry else "Deploying"
    print(f"\n{operation_mode} code for Lambda function: {args.function_name}")

    # Determine which patterns to use for finding files
    patterns = args.include if args.include else [VALID_FILE_PATTERN]

    print(f"\nUsing file patterns: {patterns}")

    # Collect all matching files
    all_files = []
    for pattern in patterns:
        matched_files = list_matching_files(pattern)
        print(f"Pattern '{pattern}' matched {len(matched_files)} files")
        all_files.extend(matched_files)

    if not all_files:
        print("No files matched the specified patterns. Aborting.")
        exit(1)

    print(f"Total files to package: {len(all_files)}")

    # Create the ZIP file - use cwd for dry run, temp dir otherwise
    if args.dry:
        zip_path = create_zip_from_paths(f"{args.function_name}.zip", all_files)
        print(f"\nDry run completed. ZIP file created at: {zip_path}")
        print("No deployment was made to AWS Lambda.")
        return

    # Validate AWS credentials after confirming we have files to deploy
    session = None
    print(f"\nValidating AWS credentials ({args.profile}) ...")
    session = validate_creds(profile_name=args.profile)
    if not session:
        print("Failed to validate AWS credentials. Deployment aborted.")
        exit(1)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        zip_path = create_zip_from_paths(temp_dir_path / ZIP_FILE_NAME, all_files)

        print_zip_contents(zip_path)

        if safe_input(f"\nSure to deploy {args.function_name}? (y/n): ", False).lower() == "y":
            print(f"Updating Lambda function: {args.function_name}")
            update_lambda_function_code(session, args.function_name, zip_path)
            print(f"Lambda function {args.function_name} updated successfully!")


if __name__ == "__main__":
    main()
