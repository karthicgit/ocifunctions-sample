import oci
import io


def ingestion_job(compartment_ocid, datasource_ocid):
    signer = oci.auth.signers.get_resource_principals_signer()
    generative_ai_agent_client = oci.generative_ai_agent.GenerativeAiAgentClient({}, signer=signer)
    generative_ai_agent_client.create_data_ingestion_job(
        create_data_ingestion_job_details=oci.generative_ai_agent.models.CreateDataIngestionJobDetails(
            data_source_id=datasource_ocid,
            compartment_id=compartment_ocid,
            description="update objectstore datasource"))


def handler(ctx, data: io.BytesIO = None):
    try:
        cfg = dict(ctx.Config())
        compartment_id = cfg['compartment_id']
        datasource_id = cfg['datasource_id']
        ingestion_job(compartment_id, datasource_id)
    except Exception as ex:
        print(ex, flush=True)
