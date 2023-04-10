OCI Function to update ORM stack variable and apply to autoscale container instance.

ORM stack code reference for container instance autoscale with Load balancer --> https://github.com/cpruvost/ocicontinst. 

If you are new to OCI functions please refer the getting started guide --> https://docs.oracle.com/en-us/iaas/developer-tutorials/tutorials/functions/func-setup-cs/01-summary.htm. 

Once the OCI function is created configure the function with the below variables

    stack_id(Oracle Resource Manager Stack OCID). 
    max_ci(maximum number of container instances limit to scale out). 
    min_ci(minimum number of container instance limit below which it wont scale in). 
    log-level(Function logging level Values allowed are 10,20,30,40,50).
    
    
 This function gets triggered by OCI alarm notification.Below repo available to create topic ,subscription and alarm using terraform.
 https://github.com/karthicgit/Terraformoci/tree/main/NotificationAlarm. 
 
 You may also create the Topic ,Subsription and Alarm using OCI console as well. 
 
 
 
 
