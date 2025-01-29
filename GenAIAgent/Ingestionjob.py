"""
Module for creating an OCI Generative AI Agent data ingestion job.

This module provides functions to interact with the OCI Generative AI Agent service,
specifically for creating data ingestion jobs.
"""

import io
import oci


def create_ingestion_job(compartment_ocid: str, datasource_ocid: str) -> None:
    """
    Creates a new data ingestion job in the specified compartment using the provided data source OCID.

    Args:
        compartment_ocid (str): The OCID of the compartment where the ingestion job will be created.
        datasource_ocid (str): The OCID of the data source used for the ingestion job.

    Returns:
        None
    """

    # Initialize the resource principals signer
    signer = oci.auth.signers.get_resource_principals_signer()

    # Create a client instance for the Generative AI Agent service
    generative_ai_agent_client = oci.generative_ai_agent.GenerativeAiAgentClient({}, signer=signer)

    # Define the details for the new ingestion job
    create_data_ingestion_job_details = oci.generative_ai_agent.models.CreateDataIngestionJobDetails(
        data_source_id=datasource_ocid,
        compartment_id=compartment_ocid,
        description="Update Object Store data source"
    )

    # Create the ingestion job
    generative_ai_agent_client.create_data_ingestion_job(create_data_ingestion_job_details)


def handler(ctx, data: io.BytesIO = None) -> None:
    """
    Handles the creation of a data ingestion job based on the provided configuration.

    Args:
        ctx: The context object containing the configuration.
        data (io.BytesIO): Optional input data (not used in this implementation).

    Returns:
        None
    """

    try:
        # Extract the compartment ID and data source ID from the configuration
        config = dict(ctx.Config())
        compartment_id = config['compartment_id']
        datasource_id = config['datasource_id']

        # Create the ingestion job
        create_ingestion_job(compartment_id, datasource_id)
    except Exception as ex:
        # Log any exceptions that occur during execution
        print(f"An error occurred: {ex}", flush=True)
