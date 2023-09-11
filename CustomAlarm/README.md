This function is a sample one to create custom alarm for Operation insights . 
How to create a function using Cloudshell --> https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsquickstartcloudshell.htm#functionsquickstart_cloudshell

NumSqlsNeedingAttention is a metric available in the namespace oci_operations_insights which can be used to trigger the alarm when sql is not performing well

Whenever the alarm is triggered the function will be invoked and a simple notification with degrading sql list as a message will be received on the subscription configured.


