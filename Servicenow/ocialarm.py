# Copyright 2023 Oracle Corporation and/or affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl

import io
import json
import logging
import requests
import oci
#import base64

from json import JSONEncoder

class ServiceNowMessage:
    def __init__(self, source, severity, event_class, resource, time_of_event, node, additional_info, description, type):
        self.source = source
        self.severity = severity
        self.event_class = event_class
        self.resource = resource
        self.time_of_event = time_of_event
        self.node = node
        self.additional_info = additional_info
        self.description = description
        self.type = type

class ServiceNowMessageEncoder(JSONEncoder):
    def default(self, obj):
        return obj.__dict__

# email notification for exceptions
def publish_notification(topic_id, msg_title, msg_body):
    signer = oci.auth.signers.get_resource_principals_signer()
    client = oci.ons.NotificationDataPlaneClient({}, signer = signer)
    msg = oci.ons.models.MessageDetails(title = msg_title, body = msg_body)
    logging.getLogger().info(msg)

    client.publish_message(topic_id, msg)

def servicenow_severity(severity):
        if severity == "CRITICAL":
            return 1
        elif severity == "WARNING":
            return 2
        elif severity == "ERROR":
            return 3
        elif severity == "INFO":
            return 4

# Usage : python code to fetch secret
# def read_secret_value(secret_id):
#     signer = oci.auth.signers.get_resource_principals_signer()
#     secret_client = oci.secrets.SecretsClient({}, signer = signer)
#
#     response = secret_client.get_secret_bundle(secret_id)
#
#     base64_Secret_content = response.data.secret_bundle_content.content
#     base64_secret_bytes = base64_Secret_content.encode('ascii')
#     base64_message_bytes = base64.b64decode(base64_secret_bytes)
#     secret_content = base64_message_bytes.decode('ascii')
#
#     return secret_content


def handler(ctx, data: io.BytesIO = None):
    cfg = dict(ctx.Config())
    try:
        body = json.loads(data.getvalue())
        # log event payload json
        #logging.getLogger().info(json.dumps(body))
        oci_severity = body.get("severity")
        snow_severity=servicenow_severity(oci_severity)


        # build the message that will be sent to ServiceNow
        message = ServiceNowMessage("OracleCloud",
                                    snow_severity,
                                    body.get("eventType"),
                                    body.get("source"),
                                    body.get("eventTime"),
                                    "",
                                    body.get("data"),
                                    "",
                                    "Alert")

        # get the token
        url = cfg["authUrl"]

        payload="grant_type=refresh_token&client_id=" + cfg["clientId"] + "&client_secret=" + cfg["clientSecret"] + "&refresh_token=" + cfg["refreshToken"]
        #logging.getLogger().info("Payload: " + payload)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        oauth_response = requests.request("POST", url, headers=headers, data=payload)
        auth_body = json.loads(oauth_response.text)

        access_token = auth_body.get("access_token")

        service_now_json = ServiceNowMessageEncoder().encode(message)
        logging.getLogger().info("Message: " + service_now_json)

        servicenow_post_url = cfg["serviceNowUrl"]
        access_token = "Bearer " + access_token
        headers = {
            'Content-Type': 'application/json',
            'Authorization' : access_token,
        }
        logging.getLogger().info("Headers: " + str(headers))

        response = requests.request("POST", servicenow_post_url, headers=headers, data=service_now_json)
        logging.getLogger().info("Response Code: " + str(response.status_code))
        logging.getLogger().info("Response: " + response.text)
    except (Exception, ValueError) as ex:
        exception_message = str(ex)
        logging.getLogger().info('error: ' + exception_message)

        # sending the exception on the notification topic
        error_topic_id = cfg["error_topic_id"]
        publish_notification(error_topic_id, "Error sending messages", exception_message)
