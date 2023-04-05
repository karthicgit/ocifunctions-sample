import oci
import json,io
from fdk import response

signer = oci.auth.signers.get_resource_principals_signer()
resource_manager_client = oci.resource_manager.ResourceManagerClient(config={},signer=signer)

def update_stack_and_apply(stack_id):

    get_stack_response = resource_manager_client.get_stack(
        stack_id=stack_id)
    stack_variables=get_stack_response.data.variables
    #existing_var=stack_variables['<variablekey>']
    #Pass key value pair to be added/modified to the ORM variables
    new_var={'key': 'new_value'}
    stack_variables.update(new_var)

    print(f"Updating variable of the stack with OCID {stack_id}")
    resource_manager_client.update_stack(
        stack_id=stack_id,
        update_stack_details=oci.resource_manager.models.UpdateStackDetails(
            variables=stack_variables))

    resource_manager_client.create_job(
        create_job_details=oci.resource_manager.models.CreateJobDetails(
            stack_id=stack_id,
            job_operation_details=oci.resource_manager.models.CreateApplyJobOperationDetails(
                operation="APPLY",
                execution_plan_strategy="AUTO_APPROVED")))
    return f"Updated stack and applied job with updated variable"


def handler(ctx, data: io.BytesIO=None):
    alarm_msg = {}
    cfg = ctx.Config()
    stack_id=cfg['stack_id']

    try:
        alarm_msg = json.loads(data.getvalue())
        print("INFO: Alarm message: ")
        print(alarm_msg, flush=True)
    except (Exception, ValueError) as ex:
        print(str(ex), flush=True)

    if alarm_msg['alarmMetaData'][0]['status'] == "FIRING" and alarm_msg['type'] in ["REPEAT","OK_TO_FIRING"] and "CIscaleout" in alarm_msg["title"]:
        autoscale="scaleout"
        func_response = update_stack_and_apply(stack_id,autoscale,max_ci,min_ci,scale_by)
        print("INFO: ", func_response, flush=True)
    elif alarm_msg['alarmMetaData'][0]['status'] == "FIRING" and alarm_msg['type'] in ["REPEAT","OK_TO_FIRING"] and "CIscalein" in alarm_msg["title"]:
        autoscale="scalein"
        func_response = update_stack_and_apply(stack_id,autoscale,max_ci,min_ci,scale_by)
        print("INFO: ", func_response, flush=True)
    else:
        print("Nothing to do")
        func_response = "Nothing to do, alarm is not FIRING"

    return response.Response(
        ctx,
        response_data=func_response,
        headers={"Content-Type": "application/json"}
    )
