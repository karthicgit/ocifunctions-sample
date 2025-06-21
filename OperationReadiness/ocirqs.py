import oci
import threading
from typing import Dict

# Define the OCI configuration
config = oci.config.from_file()

# Initialize the OCI Resource Search client
search_client = oci.resource_search.ResourceSearchClient(config)

# Define the search queries
search_queries = {
    "Alarms": "query alarm resources where lifecycleState = 'ACTIVE'",
    "Budget": "query budget resources where lifecycleState = 'ACTIVE'",
    "compute_instances_running": "query instance resources where lifecycleState = 'RUNNING'",
    "compute_instances_stopped": "query instance resources where lifecycleState = 'STOPPED'",
    "compute_instances_terminated": "query instance resources where lifecycleState = 'TERMINATED'",
    "Quota_policies": "query quota resources",
    "Volume_backup": "query VolumeBackupPolicy resources where lifecycleState = 'AVAILABLE'"
}


def execute_search_query(query_name: str, query: str) -> int:
    """Execute a search query and return the count of results."""
    try:
        response = search_client.search_resources(
            oci.resource_search.models.StructuredSearchDetails(type="Structured", query=query))
        if response.data and response.data.items:
            return len(response.data.items)
        else:
            return 0
    except oci.exceptions.ServiceError as e:
        print(f"Error executing query '{query_name}': {e}")
        return 0


def summarize_results(oci_search_queries: Dict[str, str]) -> Dict[str, int]:
    """Summarize the results of multiple search queries using threading."""
    results = {}
    threads = []

    def execute_query(query_name: str, query: str):
        results[query_name] = execute_search_query(query_name, query)

    for query_name, query in oci_search_queries.items():
        thread = threading.Thread(target=execute_query, args=(query_name, query))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return results


if __name__ == "__main__":
    final_results = summarize_results(search_queries)
    print("\nOCI Resource Summary:")
    for resource, count in final_results.items():
        print(f"  {resource}: {count} found")
