# Copyright 2023 Oracle Corporation and/or affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl


import io
import oci
import base64

import sys
import requests
import json
import logging


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

# Usage: function to obtain a new OAuth 2.0 access token
def get_new_token(snow_url,client_id,client_secret,refresh_token):

    auth_server_url = f'{snow_url}/oauth_token.do'
    client_id = read_secret_value(client_id)
    client_secret = read_secret_value(client_secret)
    refresh_token = read_secret_value(refresh_token)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    token_payload = {'grant_type': 'refresh_token','refresh_token': refresh_token,'client_id' : client_id,'client_secret' : client_secret}
    try:
        token_response = requests.post(auth_server_url, headers=headers, data=token_payload ,allow_redirects=False)
    except Exception as auth_exception:
        print(auth_exception)

    if token_response.status_code !=200:
        print("Failed to obtain token from the OAuth 2.0 server", file=sys.stderr)
        sys.exit(1)

    print("Successfully obtained a new token")
    tokens = json.loads(token_response.text)
    access_token = tokens['access_token']
    return f'Bearer {access_token}'

def servicenow_severity(severity):
        if severity == "CRITICAL":
            return "1"
        elif severity == "WARNING":
            return "2"
        elif severity == "ERROR":
            return "3"
        elif severity == "INFO":
            return "4"


def handler(ctx, data: io.BytesIO = None):
    cfg = dict(ctx.Config())

    #fetch details from function config
    snow_url = cfg['snow_url']
    client_id = cfg['snow_client_id']
    client_secret = cfg['snow_client_secret']
    refresh_token = cfg['snow_refresh_token']

    try:
        body = json.loads(data.getvalue())
        oci_severity = body.get("severity")
        snow_severity=servicenow_severity(oci_severity)
        snow_short_desc = body.get("title")
        snow_desc = body.get("body")
        alarm_type = body.get("type")
        snow_comments = body["alarmMetaData"][0]["dimensions"][0]["resourceDisplayName"]

        snow_message_json = {
            "urgency" : snow_severity,
            "impact" : snow_severity,
            "short_description": snow_short_desc,
            "description": snow_desc,
            "caller_id" : "OCI",
            "comments": f'Incident created for resource {snow_comments}',
            "assignment_group": "Operations"
        }

        access_token = get_new_token(snow_url,client_id,client_secret,refresh_token)

        snow_incident_url = f'{snow_url}/api/now/table/incident'
        headers = {
            'Authorization' : access_token
        }
        if alarm_type in ["OK_TO_FIRING"]:
            response_incident = requests.post(snow_incident_url, headers=headers, json=snow_message_json)
            logging.getLogger().info("Response Code: " + str(response_incident.status_code))
        else:
            print("Alarm type is not OK_TO_FIRING")
    except (Exception, ValueError) as ex:
        print(ex)
