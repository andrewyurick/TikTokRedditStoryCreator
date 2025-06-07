# polly_test.py
from dotenv import load_dotenv
import os
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError

# 1. Load your .env
load_dotenv()

# 2. Grab region (and keys, if you didn’t configure a default session)
region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
if not region:
    raise RuntimeError("AWS_REGION not set in .env or environment")

# 3. Create the Polly client with an explicit region
polly = boto3.client(
    "polly",
    region_name=region,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# 4. Test it
try:
    voices = polly.describe_voices()
    print("Polly is reachable! Voices available:", len(voices["Voices"]))
except (BotoCoreError, NoCredentialsError) as e:
    print("Error connecting to Polly:", e)
