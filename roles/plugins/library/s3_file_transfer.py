#!/usr/bin/env python

from __future__ import (division, print_function, absolute_import)

ANSIBLE_METADATA = {
	'version': '2.9.27',
	'status': ['preview'],
	'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: s3_file_transfer

short_description: Uplaod File to S3

version_added: "1.0"

description:
    - "The main function of the module is to upload file to S3（like Minio、Amazon S3、Alibaba Cloud OSS）. "

options:
    endpoint_url:
        description:
            - S3 Service Access Address ( s3_host:s3_api_port ).
        required: True
        type: str
    ak:
        description:
            - Accessing the AccessKeyId of S3 services.
        required: True
        type: str
    sk:
        description:
            - Accessing the Signature of S3 services.
        required: True
        type: str
    src:
        description:
            - The absolute path of the source file to upload or download.
        required: true
        type: str
    dest:
        description:
            - The absolute path of the target file to upload or download.
        required: True
        type: str
    bs:
        description:
            - Size per write ( 1024 * 1024 * bs )M/s.
        required: false
        type: int
        default: 5
    concurrency:
        description:
            - Write concurrency.
        required: false
        type: int
        default: 10
    read_timeout:
        description:
            - Time out for receiving data ( Second ).
        required: false
        type: int
        default: 60
    connect_timeout:
        description:
            - The timeout for establishing a connection ( Second ).
        required: false
        type: int
        default: 10
    state:
        description:
            - Define operation types for upload or download.
        required: false
        type: str
        default: upload

        
author:
    - Tianciwang
'''

EXAMPLES = '''
# Upload File
- name: Upload files locally to S3
  s3_file_transfer:
    endpoint_url: "0.0.0.0:80"
    ak: "admin"
    sk: "Admin1234"
    src: "/path/to/source/filename"
    dest: "bucketName/object_path/object_name"
    
# Download File
- name: Download files from S3 to local
  s3_file_transfer:
    endpoint_url: "0.0.0.0:80"
    ak: "admin"
    sk: "Admin1234"
    dest: "/path/to/source/filename"
    src: "bucketName/object_path/object_name"
    state: "download"
'''

RETURN = '''
msg:
    description: Incoming raw data parameters (exception information or upload result information, depending on the method used).
    type: str
    returned: when initializing S3 connection objects or uploading or downloading data
src:
    description: Absolute path to source file
    type: str
    returned: source file path
dest:
    description: Absolute path to destination file
    type: str
    returned: destination file path
'''

from ansible.module_utils.basic import AnsibleModule

try:
	import boto3, os, botocore

	HAS_LIB = True
except ImportError:
	HAS_LIB = False


class S3Api():
	def __init__(self, module):
		self.protocol = "http://"
		self.service_type = "s3"
		self.endpoint_url = module.params["endpoint_url"]
		self.ak = module.params["ak"]
		self.sk = module.params["sk"]
		self.connect_timeout = module.params["connect_timeout"]
		self.read_timeout = module.params["read_timeout"]
		self.access_obj = self.s3_check_access

	@property
	def s3_conn(self):
		s3_client = boto3.client(
			self.service_type,
			endpoint_url=self.protocol + self.endpoint_url,
			aws_access_key_id=self.ak,
			aws_secret_access_key=self.sk,
			config=botocore.config.Config(
				connect_timeout=self.connect_timeout,
				read_timeout=self.read_timeout
			)
		)
		return s3_client

	@property
	def s3_check_access(self):
		try:
			self.s3_conn.list_buckets()
			return self.s3_conn
		except botocore.exceptions.ClientError as e:
			if e.response['Error']['Code'] == 'InvalidAccessKeyId':
				# InvalidAccessKeyId
				return "Invalid access key id: " + self.ak
			elif e.response['Error']['Code'] == 'InvalidEndpoint':
				# Invaild Endpoint URL
				return "Invalid endpoint: " + self.endpoint_url
			elif e.response['Error']['Code'] == 'SignatureDoesNotMatch':
				# Invaild Signature
				return "Invalid signature: " + self.sk
			else:
				return "ClientError Unknown error occurred: " + str(e)
		except Exception as e:
			return "Unknown error occurred: " + str(e)


class AnsibleS3Upload(S3Api):
	def __init__(self, module):
		super().__init__(module)
		self.module = module
		self.result = dict(
			changed=False,
			msg=''
		)
		self.action = ''

	@property
	def callback_s3_conn(self):
		if isinstance(self.access_obj, botocore.client.BaseClient):
			return self.access_obj
		else:
			self.result["msg"] = self.access_obj
			self.module.fail_json(**self.result)

	def run(self):
		if self.module.check_mode:
			self.module.exit_json(**self.result)

		if not HAS_LIB:
			self.module.fail_json(
				msg='boto3 library is required for this module. To install, use `pip install boto3 botocore`')

		self.define_action()
		self.run_action()
		self.module.exit_json(**self.result)

	def define_action(self):
		if self.module.params["state"] == "upload":
			self.action = 's3_upload_files'
		elif self.module.params["state"] == "download":
			self.action = 's3_download_files'
		else:
			self.module.fail_json(msg='invalid parameters combination, only use upload or download',
								  **self.module.params)

	def run_action(self):
		action = getattr(self, self.action)
		action()

	@property
	def parse_module_args(self):
		src_file = self.module.params["src"]
		dest_file = self.module.params["dest"]
		bs_count = self.module.params["bs"]
		concurrency = self.module.params["concurrency"]
		return src_file, dest_file, bs_count, concurrency

	def s3_upload_files(self):
		"""Upload files locally to S3"""
		src_file, dest_file, bs_count, concurrency = self.parse_module_args
		with open(src_file, 'rb') as upload_src_file:
			self.callback_s3_conn.upload_fileobj(
				upload_src_file,
				dest_file.split("/")[0],
				'/'.join(dest_file.split("/")[1:]),
				Config=boto3.s3.transfer.TransferConfig(
					multipart_chunksize=bs_count * 1024 * 1024,
					max_concurrency=concurrency,
				)
			)
		self.result["changed"] = True
		self.result["src"] = src_file
		self.result["dest"] = dest_file
		self.result["msg"] = "Upload File Successfully."

	def s3_download_files(self):
		"""Download files from S3 to local"""
		src_file, dest_file, bs_count, concurrency = self.parse_module_args
		self.callback_s3_conn.download_file(
			src_file.split("/")[0],
			'/'.join(src_file.split("/")[1:]),
			dest_file
		)
		self.result["changed"] = True
		self.result["src"] = src_file
		self.result["dest"] = dest_file
		self.result["msg"] = "Download File Successfully."


def run_module():
	''' Define Modeule Args'''
	module_args = dict(
		src=dict(type="str", require=True),
		dest=dict(type="str", require=True),
		ak=dict(type="str", require=True),
		sk=dict(type="str", require=True),
		bs=dict(type=int, require=False, default=5),
		concurrency=dict(type=int, require=False, default=10),
		connect_timeout=dict(type=int, require=False, default=10),
		read_timeout=dict(type=int, require=False, default=60),
		state=dict(type="str", require=False, default="upload"),
		endpoint_url=dict(type="str", require=False, default="127.0.0.1:80"),
	)
	module = AnsibleModule(
		argument_spec=module_args,
		supports_check_mode=True
	)
	AnsibleS3Upload(module).run()


def main():
	run_module()


if __name__ == '__main__':
	main()

