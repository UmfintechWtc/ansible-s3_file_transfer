# ansible-s3_file_transfer

### Introduce
Ansible module to upload object to S3 or download object to local compatible object storage server (https://minio.io)

### My use case

In order to automate some things related to S3, I must use the [mc binary file](https://min.io/docs/minio/linux/reference/minio-mc.html?ref=docs).
To upload or download files, I need to use the [mc Configuration Settings](https://min.io/docs/minio/linux/reference/minio-mc-admin/mc-admin-config.html#id4)
And I found that the target machine also relies on the [mc binary file], but this is not secure enough. Each machine needs to have an authentication file for the [mc binary file].
So, ... I writed down a module. For now it is deadly simple,  only uploading or downloading files, but it works.

If you want an example of what it looks like, then this is the roles which embbed it:
```yaml
---
- name: Upload local file to S3 Server
  s3_file_transfer:
    endpoint_url: "{{ s3_endpoint_url }}"
    ak: "{{ s3_ak }}"
    sk: "{{ s3_sk }}"
    src: "/root/zabbix_agentd.log"
    dest: "my-bucket/sub-bucket1/zabbix_agentd.log"
    state: "upload"

- name: Download S3 Server file to local
  s3_file_transfer:
    endpoint_url: "{{ s3_endpoint_url }}"
    ak: "{{ s3_ak }}"
    sk: "{{ s3_sk }}"
    src: "my-bucket/sub-bucket1/zabbix_agentd.log"
    dest: "/root/zabbix_agentd.log"
    state: "download"
```

### Install

---

Install it via ansible-galaxy (recommended):

```bash
ansible-galaxy collection install marmorag.ansodium
```
###### *__NOTE__: Installing collections with ansible-galaxy is only supported in ansible 2.9+ and Python Version >= 3.6*

You will need the `boto3, botocore` Python>=3.7 module to be installed.
```bash
pip install boto3 botocore
```

Or use the provided `install` roles

```yaml
roles:
    - { role: .ansodium.install }
```

---
Install it manually:

Refering to [ansible docs](https://docs.ansible.com/ansible/latest/dev_guide/developing_locally.html#adding-a-module-locally) to install a module, either :

- add directory to `ANSIBLE_LIBRARY` environment variable
- put it in  `~/.ansible/plugins/modules/`
- put in in `/usr/share/ansible/plugins/modules/`

```bash
git clone https://gitee.com/TianCiwang/ansible-s3upload-with-minio.git
cd ./ansible-s3upload-with-minio

mkdir -p ~/.ansible/plugins/modules
cp ./s3_file_transfer.py ~/.ansible/plugins/modules
```

Or, to use it in one playbook/role only:

- put it in a `library` directory in the directory containing your __playbook__ 
- put it in a `library` directory in the directory containing your __role__ 

In any case, you can check that module is correctly installed with

```bash
ansible-doc -t module s3_file_transfer
```

Of course `boto3, botocore` python package is required in that case too.

### Usage

---

#### Upload file
```yaml
- name: Upload local file to S3 Server
  s3_file_transfer:
    endpoint_url: "{{ s3_endpoint_url }}"
    ak: "{{ s3_ak }}"
    sk: "{{ s3_sk }}"
    src: "/root/zabbix_agentd.log"
    dest: "my-bucket/sub-bucket1/zabbix_agentd.log"
    state: "upload"
```
Output format : 
```json
{
  "changed": true, 
  "dest": "my-bucket/sub-bucket1/zabbix_agentd.log", 
  "msg": "Upload File Successfully.", 
  "src": "/root/zabbix_agentd.log"
}
```

---
#### Download file

```yaml
- name: Download S3 Server file to local
  s3_file_transfer:
    endpoint_url: "{{ s3_endpoint_url }}"
    ak: "{{ s3_ak }}"
    sk: "{{ s3_sk }}"
    src: "my-bucket/sub-bucket1/zabbix_agentd.log"
    dest: "/root/zabbix_agentd.log"
    state: "download"
```
Output format : 
```json
{
  "changed": true, 
  "dest": "/root/zabbix_agentd.log", 
  "gid": 0, 
  "group": "root", 
  "mode": "0644", 
  "msg": "Download File Successfully.", 
  "owner": "root", 
  "size": 3702, 
  "src": "my-bucket/sub-bucket1/zabbix_agentd.log", 
  "state": "file", 
  "uid": 0
}
```
