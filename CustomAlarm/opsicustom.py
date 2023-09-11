# Copyright 2023 Oracle Corporation and/or affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl

import io
from datetime import datetime,timedelta
import oci
import json

def opsi_sqlstatistics(compartment_id,resource_type,start_time):
    try:
        signer = oci.auth.signers.get_resource_principals_signer()
        opsi_client = oci.opsi.OperationsInsightsClient({},signer=signer)
        summarize_sql_insights_response = opsi_client.summarize_sql_statistics(
            compartment_id=compartment_id,
            database_type=[resource_type],
            time_interval_start=datetime.strptime(
                start_time,
                "%Y-%m-%dT%H:%M:%S.%fZ")
            #category=["CHANGING_PLANS","INEFFICIENT"]
        )
        str_summary = str(summarize_sql_insights_response.data.items)
        json_summary = json.loads(str_summary)
        sql_identifier_list = []
        for i in range(len(json_summary)):
            sql_identifier_list.append(json_summary[i]['sql_identifier'])
        return sql_identifier_list
    except Exception as opsi_exception:
        print(opsi_exception)


def ons_publish(compartment_id=None, **kwargs):
    TWO_HOUR_BEFORE = (datetime.utcnow() - timedelta(minutes=120)).isoformat() + 'Z'
    try:
        signer = oci.auth.signers.get_resource_principals_signer()
        ons_client = oci.ons.NotificationDataPlaneClient({},signer=signer)
        resource_type = kwargs.get('resource_type')
        start_time = TWO_HOUR_BEFORE
        topic_id = kwargs.get('topic_id')
        resource_display_name = kwargs.get('resource_display_name')

        sql_list = opsi_sqlstatistics(compartment_id, resource_type,start_time)
        body = f'SQL Identifier having issues are {sql_list}'
        print("Publishing message to ONS topic")
        ons_client.publish_message(
            topic_id=topic_id,
            message_details=oci.ons.models.MessageDetails(
                body=body,
                title=f"SQL Degradation for {resource_display_name}"))
    except Exception as ons_exception:
        print(ons_exception)

def handler(ctx, data: io.BytesIO = None):
    cfg = dict(ctx.Config())

    # fetch details from function config
    compartment_id = cfg['compartment_id']
    topic_id = cfg['topic_id']

    try:
        body = json.loads(data.getvalue())
        alarm_type = body.get("type")
        #start_time = body.get("timestamp")

        if alarm_type in ["OK_TO_FIRING"]:
            #resource_id = body["alarmMetaData"][0]["dimensions"][0]["resourceId"]
            resource_display_name = body["alarmMetaData"][0]["dimensions"][0]["resourceDisplayName"]
            resource_type = body["alarmMetaData"][0]["dimensions"][0]["resourceType"]

            ons_publish(compartment_id=compartment_id,
                        resource_display_name=resource_display_name, topic_id=topic_id,resource_type=resource_type)
        else:
            print("Alarm type is not in OK_TO_FIRING state")
    except (Exception, ValueError) as ex:
        print(ex)
