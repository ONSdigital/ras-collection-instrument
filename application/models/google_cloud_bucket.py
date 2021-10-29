import logging
from hashlib import sha256

import structlog
from flask import current_app
from google.cloud import storage
from google.cloud.exceptions import NotFound

from application.exceptions import RasError

log = structlog.wrap_logger(logging.getLogger(__name__))


class GoogleCloudSEFTCIBucket:
    def __init__(self, config):
        self.project_id = config["GOOGLE_CLOUD_PROJECT"]
        self.bucket_name = config["SEFT_DOWNLOAD_BUCKET_NAME"]
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)
        self.prefix = config["SEFT_DOWNLOAD_BUCKET_FILE_PREFIX"]

    def upload_file_to_bucket(self, file):
        path = file.filename
        if self.prefix != "":
            path = self.prefix + "/" + path
        log.info("Uploading SEFT CI to GCP bucket: " + path)
        key = current_app.config.get("ONS_CRYPTOKEY", None)
        if key is None:
            log.error("Customer defined encryption key is missing.")
            raise RasError("can't find customer defined encryption, hence can't perform this task", 500)
        customer_supplied_encryption_key = sha256(key.encode("utf-8")).digest()
        blob = self.bucket.blob(blob_name=path, encryption_key=customer_supplied_encryption_key)
        blob.upload_from_file(file_obj=file.stream, rewind=True)
        log.info("Successfully put SEFT CI in bucket")
        return

    def download_file_from_bucket(self, file_location: str):
        if self.prefix != "":
            path = self.prefix + "/" + file_location
        else:
            path = file_location
        log.info("Downloading SEFT CI from GCP bucket: " + path)
        key = current_app.config.get("ONS_CRYPTOKEY", None)
        if key is None:
            log.error("Customer defined encryption key is missing.")
            raise RasError("can't find customer defined encryption, hence can't perform this task", 500)
        customer_supplied_encryption_key = sha256(key.encode("utf-8")).digest()
        blob = self.bucket.blob(blob_name=path, encryption_key=customer_supplied_encryption_key)
        file = blob.download_as_bytes()
        log.info("Successfully downloaded SEFT CI from GCP bucket")
        return file

    def delete_file_from_bucket(self, file_location: str):
        if self.prefix != "":
            path = self.prefix + "/" + file_location
        else:
            path = file_location
        log.info("Deleting SEFT CI from GCP bucket: " + path)
        try:
            self.bucket.delete_blob(path)
            log.info("Successfully deleted SEFT CI file")
        except NotFound:
            log.error("SEFT CI file not found when attempting to delete")
        return
