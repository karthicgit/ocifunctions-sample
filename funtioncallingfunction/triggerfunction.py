import io
import oci
import json
from fdk import response
from datetime import datetime, timedelta

today = datetime.now()
yesterday = today - timedelta(days=1)
day_before_yesterday = today - timedelta(days=2)


def format_date(date):
    return date.strftime('%Y-%m-%d')

def handler(ctx, data: io.BytesIO = None):
    try:
        cfg = ctx.Config()
        compartment_id = cfg.get('COMPARTMENT_ID')
        region = cfg.get('REGION')
        namespace = cfg.get('NAMESPACE')
        target_bucket = cfg.get('TARGET_BUCKET')
        source_bucket = cfg.get('SOURCE_BUCKET')
        finops_body = {
            "COMPARTMENT_ID": compartment_id,
            "REGION": region,
            "NAMESPACE": namespace,
            "SOURCE_BUCKET": source_bucket,
            "TARGET_BUCKET": target_bucket,
            "START_DATE": format_date(day_before_yesterday),
            "END_DATE": format_date(yesterday)
        }
        function_body = json.dumps(finops_body)
        function_endpoint = cfg.get('FUNCTION_ENDPOINT')
        function_ocid = cfg.get('FUNCTION_OCID')
    except Exception as ex:
        print('ERROR: Missing key in payload', ex, flush=True)
        raise

    signer = oci.auth.signers.get_resource_principals_signer()
    client = oci.functions.FunctionsInvokeClient(config={}, signer=signer, service_endpoint=function_endpoint,timeout=280)
    resp = client.invoke_function(function_id=function_ocid, invoke_function_body=function_body)
    print(resp.data.text, flush=True)

    return response.Response(
        ctx,
        response_data=resp.data.text,
        headers={"Content-Type": "application/json"}
    )
