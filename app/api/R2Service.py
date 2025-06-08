import boto3
from botocore.client import Config
from app.configuration.settings import Configuration
from fastapi import HTTPException
import logging

configuration = Configuration()

class R2Service:
    def __init__(self):
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=configuration.endpoint_url_r2,
                aws_access_key_id=configuration.aws_access_key_id_aws,
                aws_secret_access_key=configuration.aws_secret_access_key_aws,
                config=Config(signature_version='s3v4'),
                region_name='auto'
            )
            self.bucket_name = configuration.r2_bucket_name
            self.public_url = configuration.r2_url_public
        except Exception as e:
            logging.error(f"Erro ao configurar cliente R2: {str(e)}")
            raise

    async def upload_file(self, file_content: bytes, file_name: str, content_type: str) -> str:
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=file_content,
                ContentType=content_type
            )
            return f"{self.public_url}/{file_name}"
        except Exception as e:
            logging.error(f"Erro ao fazer upload para R2: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao fazer upload da imagem: {str(e)}"
            )

    async def delete_file(self, file_name: str) -> bool:
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=file_name
            )
            return True
        except Exception as e:
            logging.error(f"Erro ao deletar arquivo do R2: {str(e)}")
            return False