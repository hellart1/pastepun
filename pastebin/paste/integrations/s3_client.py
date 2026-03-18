from django.conf import settings
import boto3


class S3Storage:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            endpoint_url = settings.AWS_S3_ENDPOINT_URL,
        )

        self.bucket = settings.AWS_STORAGE_BUCKET_NAME

    def upload_text(self, key, text):
        return self.s3.put_object(Bucket=self.bucket, Key=f"{key}.txt", Body=text)

    def get_content(self, key):
        response = self.s3.get_object(Bucket=self.bucket, Key=f"{key}.txt")
        return response['Body'].read().decode('utf-8')

    def get_size(self, key):
        response = self.s3.head_object(Bucket=self.bucket, Key=f"{key}.txt")
        return response['ContentLength']

    def delete_object(self, key):
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=f"{key}.txt")
        except Exception as e:
            print(f"Ошибка при удалении объекта {key} из S3: {e}")
            raise e
