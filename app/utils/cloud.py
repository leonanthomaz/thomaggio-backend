from app.configuration.settings import Configuration
import boto3
from botocore.client import Config

configuration = Configuration()

s3_client = boto3.client(
    's3',
    endpoint_url=configuration.endpoint_url_r2,
    aws_access_key_id=configuration.aws_access_key_id_aws,
    aws_secret_access_key=configuration.aws_secret_access_key_aws,
    config=Config(signature_version='s3v4'),
    region_name='auto'
)

def upload_file_to_s3(file_content, filename, content_type):
    bucket_name = 'productimages'

    s3_client.put_object(
        Bucket=bucket_name,
        Key=filename,
        Body=file_content,
        ContentType=content_type,
        ACL='public-read'  # ou sem isso se for usar URL assinada
    )

    return f"https://{bucket_name}.{s3_client.meta.endpoint_url}/{filename}"
