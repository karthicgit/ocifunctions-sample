from builtins import object, len
import time
import sys
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY

import oci
from datetime import datetime, timezone, timedelta

compartment_id = sys.argv[1]

# Instance principal
signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
monitoring_client = oci.monitoring.MonitoringClient(config={}, signer=signer)

#These metrics details are fetched using listmetrics API.
COMPUTE_METRICS = [
    "CpuUtilization",
    "DiskBytesRead",
    "DiskBytesWritten",
    "DiskIopsRead",
    "DiskIopsWritten",
    "LoadAverage",
    "MemoryAllocationStalls",
    "MemoryUtilization",
    "NetworksBytesIn",
    "NetworksBytesOut"
]

VCN_METRICS1 = [
    "VnicConntrackIsFull",
    "VnicConntrackUtilPercent",
    "VnicEgressDropsConntrackFull",
    "VnicEgressDropsSecurityList",
    "VnicEgressDropsThrottle",
    "VnicEgressMirrorDropsThrottle",
    "VnicFromNetworkBytes",
    "VnicFromNetworkMirrorBytes",
    "VnicFromNetworkMirrorPackets",
    "VnicFromNetworkPackets"
]
VCN_METRICS2 = [
    "VnicIngressDropsConntrackFull",
    "VnicIngressDropsSecurityList",
    "VnicIngressDropsThrottle",
    "VnicIngressMirrorDropsConntrackFull",
    "VnicIngressMirrorDropsSecurityList",
    "VnicIngressMirrorDropsThrottle",
    "VnicToNetworkBytes",
    "VnicToNetworkMirrorBytes",
    "VnicToNetworkMirrorPackets",
    "VnicToNetworkPackets",
]
OBJECTSTORAGE_METRICS = [
    "AllRequests",
    "ClientErrors",
    # "EnabledOLM",
    "FirstByteLatency",
    "HeadRequests",
    "ListRequests",
    "ObjectCount",
    "PutRequests",
    "StoredBytes",
    "TotalRequestLatency",
    "UncommittedParts"
]

#function to give summarize metrics for specific namespace and metrics
def metric_summary(now, one_min_before, metric_name,namespace,compartment_ocid):
    summarize_metrics_data_response = monitoring_client.summarize_metrics_data(
        compartment_id=compartment_ocid,
        summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(
            namespace=namespace,
            query=f"{metric_name}[1m].mean()",
            start_time=one_min_before,
            end_time=now))
    return summarize_metrics_data_response.data


def get_metrics():
    now = (datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    ONE_MIN_BEFORE = (datetime.utcnow() - timedelta(minutes=1)).isoformat() + 'Z'

    summarize_metrics_list = []
    for name in COMPUTE_METRICS:
        summary = metric_summary(now,ONE_MIN_BEFORE,name,"oci_computeagent",compartment_id)
        if len(summary) > 0:
            summarize_metrics_list.append(summary)
        else:
            break
    time.sleep(1)
    for name in VCN_METRICS1:
        summary = metric_summary(now,ONE_MIN_BEFORE,name,"oci_vcn",compartment_id)
        if len(summary) > 0:
            summarize_metrics_list.append(summary)
        else:
            break
    time.sleep(1)
    for name in VCN_METRICS2:
        summary = metric_summary(now,ONE_MIN_BEFORE,name,"oci_vcn",compartment_id)
        if len(summary) > 0:
            summarize_metrics_list.append(summary)
        else:
            break
    time.sleep(1)
    for name in OBJECTSTORAGE_METRICS:
        summary = metric_summary(now,ONE_MIN_BEFORE,name,"oci_objectstorage",compartment_id)
        if len(summary) > 0:
            summarize_metrics_list.append(summary)
        else:
            break
    return summarize_metrics_list


class OCIExporter(object):
    def __init__(self):
        pass

    def collect(self):
        metric_data = get_metrics()
        for metrics in metric_data:
            for metric in metrics:
                name = f'oci_{metric.name.lower()}'
                dimensions = metric.dimensions
                if dimensions.get('resourceDisplayName') is not None:
                    labels = ['resource_name']
                    resource_id = dimensions.get('resourceDisplayName')
                else:
                    labels = ['resource_id']
                    resource_id = dimensions.get('resourceId')

                metadata = metric.metadata
                description = metadata.get('displayName')
                value = metric.aggregated_datapoints[0].value

                g = GaugeMetricFamily(name=name, documentation=description, labels=labels)
                g.add_metric(labels=[resource_id], value=value)
                yield g


if __name__ == "__main__":
    start_http_server(8070)
    REGISTRY.register(OCIExporter())
    while True:
        time.sleep(1)
