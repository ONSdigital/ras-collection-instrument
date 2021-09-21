import base64
import logging
import os

import structlog
from google.cloud import storage

log = structlog.wrap_logger(logging.getLogger(__name__))


class GoogleCloudSEFTCIBucket:
    def __init__(self, config):
        self.project_id = config["GOOGLE_CLOUD_PROJECT"]
        self.bucket_name = config["SEFT_CI_BUCKET_NAME"]
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)
        self.prefix = config["SEFT_CI_BUCKET_FILE_PREFIX"]

    def upload_file_to_bucket(self, file):
        log.info("Uploading SEFT CI to GCP bucket: " + file.filename)
        if self.prefix != "":
            path = self.prefix + "/" + file.filename
        else:
            path = file.filename
        key = self.generate_encryption_key()
        encryption_key = base64.b64decode(key)
        blob = self.bucket.blob(path, encryption_key=encryption_key)
        blob.upload_from_file(file.stream)
        log.info("Successfully put SEFT CI in bucket")
        return path, key

    def download_file_from_bucket(self, file_location, key):
        log.info("Downloading SEFT CI from GCP bucket: " + file_location)
        encryption_key = base64.b64decode(key)
        blob = self.bucket.blob(file_location, encryption_key=encryption_key)
        file = blob.download_as_bytes()
        log.info("Successfully downloaded SEFT CI from GCP bucket")
        return file

    def generate_encryption_key(self):
        key = os.urandom(32)
        encoded_key = base64.b64encode(key).decode("utf-8")
        return encoded_key
