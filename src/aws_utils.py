import configparser
import os
from pathlib import Path

import boto3
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
    ProfileNotFound,
)

from .defaults import DEFAULT_PROFILE, aws_dir


def setup_aws_credentials(
    access_key=None,
    secret_key=None,
    session_token=None,
    region=None,
    output_format="json",
    profile=DEFAULT_PROFILE,
    config_location=None,
    credentials_location=None,
):
    f"""
    Set up AWS credentials and configuration for boto3 and AWS CLI.

    Args:
        access_key (str, optional): AWS access key ID
        secret_key (str, optional): AWS secret access key
        session_token (str, optional): AWS session token (for temporary credentials)
        region (str, optional): AWS region (e.g., 'us-east-1')
        output_format (str, optional): Output format for AWS CLI (json, text, table)
        profile (str, optional): AWS profile name, defaults to '{DEFAULT_PROFILE}'
        config_location (str, optional): Custom location for config file
        credentials_location (str, optional): Custom location for credentials file

    """

    if not credentials_location:
        credentials_location = aws_dir / "credentials"

    if not config_location:
        config_location = aws_dir / "config"

    credentials_location, config_location = map(Path, (credentials_location, config_location))

    # Create .aws directory if it doesn't exist
    if not aws_dir.is_dir():
        aws_dir.mkdir(parents=True)
        print(f"Created AWS config directory: {aws_dir}")

    # Update credentials file if credentials are provided
    if access_key or secret_key or session_token:
        credentials = configparser.ConfigParser()

        # Read existing credentials file if it exists
        if credentials_location.is_file():
            credentials.read(credentials_location)

        # Add or update the profile section
        if not credentials.has_section(profile):
            credentials.add_section(profile)

        if access_key:
            credentials[profile]["aws_access_key_id"] = access_key

        if secret_key:
            credentials[profile]["aws_secret_access_key"] = secret_key

        if session_token:
            credentials[profile]["aws_session_token"] = session_token

        # Write to credentials file
        with credentials_location.open("w", encoding="utf-8") as file:
            credentials.write(file)

        print(f"Updated AWS credentials for profile '{profile}' in {credentials_location}")

    # Update config file if region or output format are provided
    if region or output_format:
        config = configparser.ConfigParser()

        # Read existing config file if it exists
        if os.path.exists(config_location):
            config.read(config_location)

        # Add or update the profile section
        profile_section = f"profile {profile}" if profile != "default" else "default"
        if not config.has_section(profile_section):
            config.add_section(profile_section)

        if region:
            config[profile_section]["region"] = region

        if output_format:
            config[profile_section]["output"] = output_format

        # Write to config file
        with config_location.open("w", encoding="utf-8") as file:
            config.write(file)

        print(f"Updated AWS config for profile '{profile}' in {config_location}")

    # Set environment variables for immediate use in current session
    if access_key:
        os.environ["AWS_ACCESS_KEY_ID"] = access_key

    if secret_key:
        os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key

    if session_token:
        os.environ["AWS_SESSION_TOKEN"] = session_token

    if region:
        os.environ["AWS_DEFAULT_REGION"] = region


def validate_creds(
    aws_access_key_id=None,
    aws_secret_access_key=None,
    region_name=None,
    profile_name=None,
):
    try:
        # Create a boto3 session which will automatically look for credentials
        # in the standard locations
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            profile_name=profile_name,
        )

        # Get the credentials object
        credentials = session.get_credentials()

        # Check if credentials are available
        if credentials is None:
            print("No credentials found")
            return None

        # Verify access key, secret key, and region are set
        if credentials.access_key is None:
            print("Access key is not set")
            return None

        if credentials.secret_key is None:
            print("Secret key is not set")
            return None

        # Get the region
        region = session.region_name
        if region is None:
            print("Default region is not set")
            return None

        # If we get here, basic credential checking passed
        print("\nCredentials found in the environment:")
        print(f"Access Key ID: {credentials.access_key[:5]}...")
        print(f"Region: {region}")

        # Test credentials with an actual AWS service call
        try:
            # Try to use a simple service call that doesn't cost anything
            client = session.client("sts")
            response = client.get_caller_identity()

            print("\nCredentials validated successfully with AWS:")
            print(f"Account: {response['Account']}")
            print(f"ARN: {response['Arn']}")
            print(f"UserId: {response['UserId']}")
            return session

        except ClientError as e:
            print(f"\nCredentials found but failed validation with AWS: {e}")
            return None

    except ProfileNotFound:
        if profile_name == DEFAULT_PROFILE:
            print("\nRun --setup first to initialize credentials...")
            return None

        print(
            f"\nThe profile ({profile_name}) couldn't be found, Make sure it exists in config files"
        )
        return None

    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Credential error: {e}")
        return None


def update_lambda_function_code(session, function_name, zip_file_path):
    """
    Updates an AWS Lambda function code with a provided ZIP file.

    Parameters:
    - session: A validated boto3 session object
    - function_name: The name or ARN of the Lambda function to update
    - zip_file_path: Path to the ZIP file containing the updated code

    Returns:
    - Response from the update_function_code API call
    """

    try:
        # Create a Lambda client using the provided session
        lambda_client = session.client("lambda")

        # Read the ZIP file
        with open(zip_file_path, "rb") as zip_file:
            zip_content = zip_file.read()

        # Update the Lambda function code (default behavior is not to publish)
        response = lambda_client.update_function_code(
            FunctionName=function_name, ZipFile=zip_content
        )

        return response

    except Exception as e:
        print(f"Error updating Lambda function: {str(e)}")
