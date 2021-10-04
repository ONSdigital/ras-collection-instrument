import logging

import structlog
from google.cloud import storage

log = structlog.wrap_logger(logging.getLogger(__name__))


class GoogleCloudSEFTCIBucket:
    def __init__(self, config):
        self.project_id = config["GOOGLE_CLOUD_PROJECT"]
        self.bucket_name = config["SEFT_DOWNLOAD_BUCKET_NAME"]
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)
        self.prefix = config["SEFT_DOWNLOAD_BUCKET_FILE_PREFIX"]

    def upload_file_to_bucket(self, file):
        log.info("Uploading SEFT CI to GCP bucket: " + file.filename)
        if self.prefix != "":
            path = self.prefix + "/" + file.filename
        else:
            path = file.filename
        blob = self.bucket.blob(path)
        blob.upload_from_file(file_obj=file.stream, rewind=True)
        log.info("Successfully put SEFT CI in bucket")
        return

    def download_file_from_bucket(self, file_location):
        log.info("Downloading SEFT CI from GCP bucket: " + file_location)
        blob = self.bucket.blob(file_location)
        file = blob.download_as_bytes()
        log.info("Successfully downloaded SEFT CI from GCP bucket")
        return file
