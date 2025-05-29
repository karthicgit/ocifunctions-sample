import io
import requests
import base64
import oci

from fdk import response

# Usage : function to fetch secret from OCI vault
def read_secret_value(secret_id):
    signer = oci.auth.signers.get_resource_principals_signer()
    secret_client = oci.secrets.SecretsClient({}, signer = signer)

    response_secret = secret_client.get_secret_bundle(secret_id)


    base64_Secret_content = response_secret.data.secret_bundle_content.content
    base64_secret_bytes = base64_Secret_content.encode('ascii')
    base64_message_bytes = base64.b64decode(base64_secret_bytes)
    secret_content = base64_message_bytes.decode('ascii')

    return secret_content

def handler(ctx, data: io.BytesIO = None):
    cfg = dict(ctx.Config())
    client_id = cfg['notification_secret_id']
    url = read_secret_value(client_id)

    payload = {"key1": "value1", "key2": "value2"}

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return {"message": "POST PASS"}
    else:
        return {"message": "POST FAIL", "status_code": response.status_code}
