Telegram Bot for File Handling

This project contains a Telegram bot that allows users to send images and audio files which are then processed and stored in AWS S3. Additionally, audio files can be transcribed using AWS Transcribe. The repository includes a GitHub Actions workflow to automate the deployment of the bot on AWS ECS.
Features

Users can set a personal folder in S3 for storing their files.
Support for uploading images directly to a specified S3 bucket.
Audio files sent by the user are converted from OGG to WAV, transcribed, and the results are stored as a Word document in S3.
CI/CD pipeline using GitHub Actions for deployment to AWS ECS.

Prerequisites

AWS account with access to ECS, ECR, and S3.
Telegram bot token from BotFather.
Docker installed on your machine for local testing.
Configure AWS CLI with appropriate permissions.

Setting Up Your Environment

Clone this repository to your local machine:
    
    git clone https://github.com/yourgithub/telegram-bot-AWS-transcribe.git


Install the required Python packages:

    pip install -r requirements.txt

Set the following environment variables:
TELEGRAM_BOT_TOKEN: Your Telegram bot token.
AWS_ACCESS_KEY_ID: Your AWS access key.
AWS_SECRET_ACCESS_KEY: Your AWS secret access key.
S3_BUCKET: Your S3 bucket name where files will be stored.

Running the Bot Locally

To run the Telegram bot locally, execute the following command:

    python telegram_s3_bot.py

Deploying to AWS

The .github/workflows/deploy.yml file contains the CI/CD pipeline configuration for deploying the bot using GitHub Actions. The pipeline performs the following steps:

Build a Docker image and push it to Amazon ECR.
Deploy the updated Docker image to an ECS service using Fargate.

Ensure that the AWS credentials are configured as secrets in your GitHub repository settings.
Usage

Send /start to the bot to initiate the session.
Send a folder name to set your personal folder for storing files.
Send images or audio files to see them processed and uploaded to your designated folder in S3.

License

This project is open-source and available under the MIT License.