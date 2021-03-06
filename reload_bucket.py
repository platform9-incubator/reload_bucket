#! /bin/env python
"""
A tool to upload contents to s3 buckets
"""

import boto3
import yaml
import logging
import sys
import os
import mimetypes
import magic

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

log = logging.getLogger(__name__)


def main():
    with open('manifests.yml', 'r') as manifest:
        config = yaml.load(manifest)
    user = os.getenv('USER', 'nobody')
    base_path = config['base_path']

    # first get version from the manifest file
    version = config['version']
    # if the env variable VERSION exists, override version above
    version = os.getenv('VERSION', version)
    remote_path_root = os.path.join(base_path, version) if version else user
    # CentOS 7 is not aware of the .json extension unless we install mailcap
    # https://stackoverflow.com/questions/33354969/why-is-mimetypes-guess-typea-json-not-working-in-centos-7#33356241
    mimetypes.add_type('application/json', '.json')
    mime = magic.Magic(mime=True)

    bucket_name = config['bucket']
    endpoint = config['endpoint']

    def upload_directory(path):
        """
        A function to upload an entire directory
        """
        objects = client.list_objects(Bucket=bucket_name, Delimiter="/")
        if 'CommonPrefixes' in objects:
            prefixes = objects['CommonPrefixes']
            log.info("Directories in {0}: {1}".format(bucket_name, [str(prefix['Prefix']) for prefix in prefixes]))
            for prefix in prefixes:
                if prefix['Prefix'].split("/")[0] == remote_path_root:
                    log.info("Found an existing directory: {0}...deleting".format(remote_path_root))
                    for key in bucket.objects.filter(Prefix=remote_path_root):
                        log.info("Deleting {0}".format(key))
                        key.delete()

        for root, dirs, files in os.walk(path):
            new_root = '/'.join(root.split(os.path.sep)[1:])
            for file in files:
                filepath = os.path.join(root, file)
                remote_file_path = os.path.join(remote_path_root, new_root, file)
                content_type = mimetypes.guess_type(filepath)[0]
                if content_type is None:
                    content_type = mime.from_file(filepath)
                log.info("Uploading {0} to {1} ({2})".format(filepath, remote_file_path, content_type))
                client.upload_file(filepath, bucket_name, remote_file_path, ExtraArgs={'ACL': 'public-read',
                                                                                       'ContentType': content_type})

    client = boto3.client('s3')
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    directories = config['directories']
    log.info("Uploading contents of {0} to {1}".format(directories,
                                                       os.path.join(endpoint, bucket_name, remote_path_root)))
    for directory in directories:
        upload_directory(directory)


if __name__ == "__main__":
    main()
