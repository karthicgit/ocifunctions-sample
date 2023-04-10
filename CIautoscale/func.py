import oci
import json,io
import logging
from fdk import response

signer = oci.auth.signers.get_resource_principals_signer()
resource_manager_client = oci.resource_manager.ResourceManagerClient(config={},signer=signer)

#To set logging
def create_log_global_variable(ctx):
    #Log Level Configuration
    try:
        cfg = ctx.Config()
        log_level = cfg["log-level"]
        print("log level: " + log_level)
    except Exception as ex:
        print('ERROR: Missing configuration log level', ex, flush=True)
        raise

    try:
        if log_level == '50':
            logging.getLogger("my-function-logger").setLevel(logging.CRITICAL)
        elif log_level == '40':
            logging.getLogger("my-function-logger").setLevel(logging.ERROR)
        elif log_level == '30':
            logging.getLogger("my-function-logger").setLevel(logging.WARNING)
        elif log_level == '20':
            logging.getLogger("my-function-logger").setLevel(logging.INFO)
        elif log_level == '10':
            logging.getLogger("my-function-logger").setLevel(logging.DEBUG)
        else: 
            logging.getLogger("my-function-logger").setLevel(logging.INFO)                
                
        global log
        log = logging.getLogger("my-function-logger")

    except Exception as ex:
        print('ERROR: Problem with log level configuration', ex, flush=True)
        raise    

def update_stack_and_apply(stack_id,autoscale,max_ci,min_ci):
    get_stack_response = resource_manager_client.get_stack(
        stack_id=stack_id)
    stack_variables=get_stack_response.data.variables
    existing_var=stack_variables['ci_count']
    log.info("ci_count : " + existing_var)
    #Pass key value pair to be added/modified to the ORM variables
    if autoscale == "scaleout":
        log.info("Add 1 to : " + existing_var)
        ci_count=int(existing_var) + 1
    else:
        log.info("Minus 1 to : " + existing_var)
        ci_count=int(existing_var) - 1
    ci_count_string = str(ci_count)     
    new_var={'ci_count': ci_count_string}
    log.info(f"Update variable of the stack with OCID {stack_id}")
    stack_variables.update(new_var)

    if int(max_ci) >= ci_count >= int(min_ci):
        try:
            log.info("Update Stack Start")
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
            log.info("Update Stack End")
            return f"Updated stack and applied job with updated variable ci_count to : " + ci_count
        except Exception as ex:
            log.error(f"Update Stack Failed: {ex}") 
            return f"Update Stack Failed"         
    else:
        if ci_count > int(max_ci):
            return f"Cant go over max_ci"
        else:
            return f"Cant go below min_ci"


def handler(ctx, data: io.BytesIO=None):

    #Log Level Configuration
    create_log_global_variable(ctx)

    alarm_msg = {}
    cfg = ctx.Config()
    stack_id=cfg['stack_id']
    min_ci = cfg["min_ci"]
    max_ci = cfg["max_ci"]
    log.info("Stack Id : " + stack_id)
    log.info("min_ci : " + min_ci)
    log.info("max_ci : " + max_ci)

    try:
        alarm_msg = json.loads(data.getvalue())
        log.info(json.dumps(alarm_msg, indent=4))
        alarmMetaData = alarm_msg["alarmMetaData"]
        log.info("Status : " + alarmMetaData[0]["status"])
        log.info("type : " + alarm_msg["type"] )
    except (Exception, ValueError) as ex:
        print(str(ex), flush=True)

    if alarm_msg['alarmMetaData'][0]['status'] == "FIRING" and alarm_msg['type'] in ["REPEAT","OK_TO_FIRING"] and "CIscaleout" in alarm_msg["title"]:
        logging.info("Scale Out")
        autoscale="scaleout"
        func_response = update_stack_and_apply(stack_id,autoscale,max_ci,min_ci)
        print("INFO: ", func_response, flush=True)
    elif alarm_msg['alarmMetaData'][0]['status'] == "FIRING" and alarm_msg['type'] in ["REPEAT","OK_TO_FIRING"] and "CIscalein" in alarm_msg["title"]:
        log.info("Scale In")
        autoscale="scalein"
        func_response = update_stack_and_apply(stack_id,autoscale,max_ci,min_ci)
        print("INFO: ", func_response, flush=True)
    else:
        log.info("Nothing to do")
        func_response = "Nothing to do, alarm is not FIRING"

    return response.Response(
        ctx,
        response_data=func_response,
        headers={"Content-Type": "application/json"}
    )
