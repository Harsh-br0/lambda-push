
# lambda-push

A streamlined CLI utility for packaging and deploying Python code to AWS Lambda functions.


## Installation

```bash
pip install -U git+https://github.com/harsh-br0/lambda-push
```

## Features

- **Simple deployment**: Package and deploy Python files to Lambda with a single command
- **Customizable file selection**: Include specific files using glob patterns
- **Credential management**: Built-in AWS credential setup and validation
- **Dry run mode**: Create deployment packages without uploading to AWS

## Usage

### Basic Usage

Deploy all Python files to a Lambda function:

```bash
lambda-push my-function-name
```

### Custom File Selection

Include specific files or patterns:

```bash
lambda-push my-function-name --include "*.py" --include "modules/**/*.py"
```

### Dry Run

Create the ZIP package without deploying to AWS:

```bash
lambda-push my-function-name --dry
```

### AWS Credentials Setup

Configure AWS credentials for deployment:

```bash
lambda-push --setup
```

## Command Line Arguments

| Argument | Description |
|----------|-------------|
| `function_name` | Name of the AWS Lambda function to update |
| `--include PATTERN` | Glob pattern to include files (can be used multiple times) |
| `--dry` | Create the ZIP file without deploying to Lambda |
| `--setup` | Configure AWS credentials |

## Examples

### Deploy Specific Files

```bash
# Deploy only handler.py and utils directory
lambda-push my-function --include "handler.py" --include "utils/**/*.py"
```

### Create Package Without Deploying

```bash
# Create a ZIP file named "my-function.zip" without deploying
lambda-push my-function --dry
```

## AWS Credentials

The tool requires properly configured AWS credentials with permissions to update Lambda functions. You can set up credentials using:

1. The `--setup` flag which guides you through the process
2. AWS CLI's `aws configure` command
3. Environment variables
4. AWS credentials file

## Requirements

- Python 3.6+
- AWS account with appropriate permissions
- Boto3