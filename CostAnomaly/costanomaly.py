import oci,io
from datetime import datetime, timedelta, timezone


def date_formatter(day):
    return day.isoformat('T', 'milliseconds') + 'Z'


today = datetime.now().replace(microsecond=0, second=0, minute=0, hour=0)
yesterday = today - timedelta(days=1)
day_before_yesterday = today - timedelta(days=2)


def ons_publish(**kwargs):
    try:
        signer = oci.auth.signers.get_resource_principals_signer()
        ons_client = oci.ons.NotificationDataPlaneClient(config={}, signer=signer)

        topic_ocid = kwargs.get('topic_id')
        percent_increase = kwargs.get('increase_percent')
        alarm_body = kwargs.get('increased_services')

        print("Publishing message to ONS topic", flush=True)
        ons_client.publish_message(
            topic_id=topic_ocid,
            message_details=oci.ons.models.MessageDetails(
                body=alarm_body,
                title=f"Cost increased by {percent_increase}%"))
    except Exception as ons_exception:
        print(ons_exception)


def usage_report(start_time, end_time, granularity):
    signer = oci.auth.signers.get_resource_principals_signer()
    usage_api_client = oci.usage_api.UsageapiClient(config={}, signer=signer)

    request_summarized_usages_response = usage_api_client.request_summarized_usages(
        request_summarized_usages_details=oci.usage_api.models.RequestSummarizedUsagesDetails(
            tenant_id=signer.tenancy_id,
            time_usage_started=date_formatter(start_time),
            time_usage_ended=date_formatter(end_time),
            granularity=granularity,
            group_by=["service", "compartmentName"],
            compartment_depth=1,
            is_aggregate_by_time=False,
            query_type="COST"))
    usage_data = request_summarized_usages_response.data.items

    total_usage = 0
    service_cost = []
    for cost in usage_data:
        if cost.computed_amount is not None and cost.computed_amount > 0:
            service_cost.append(
                {"Service": cost.service, "Cost": cost.computed_amount, "Compartment": cost.compartment_name})
            total_usage = total_usage + cost.computed_amount

    max_service_cost = max(service_cost, key=lambda x: x['Cost'])
    print(f'Max_Service={max_service_cost["Service"]}:{max_service_cost["Cost"]}', flush=True)
    return int(total_usage), service_cost


def cost_anomaly(topic_id):
    old_total, old_service_cost = usage_report(day_before_yesterday, yesterday, "DAILY")
    print('#****************************************************************')
    curr_total, curr_service_cost = usage_report(yesterday, today, "DAILY")
    difference = (curr_total - old_total) / curr_total
    if difference < 0:
        print(f"################################################################")
        print(f"Current total is less than previous day total by {round(abs(difference * 100), 2)}%", flush=True)
        print(f"################################################################")

    else:
        print(f"################################################################")
        print(f"Current total is greater than previous day total by {round(abs(difference * 100), 2)}%", flush=True)
        difference = f"{round(abs(difference * 100), 2)}"
        print(f"################################################################")
        # Services with increased cost
        increased_services = []
        for curr_cost in curr_service_cost:
            for old_cost in old_service_cost:
                if curr_cost['Service'] == old_cost['Service'] and curr_cost['Compartment'] == old_cost[
                    'Compartment'] and int(curr_cost['Cost']) > int(old_cost['Cost']):
                    increased_services.append(curr_cost)
                    break

        if increased_services:
            body = "Services with Increased Cost\n"
            for service in increased_services:
                print(f"Service: {service['Service']}, Cost: {service['Cost']}, Compartment: {service['Compartment']}")
                body = body + f"{service['Service']},{service['Cost']},{service['Compartment']}\n"
            ons_publish(increase_percent=difference, increased_services=body, topic_id=topic_id)
        else:
            print("No services with increased cost found.")


def handler(ctx,data: io.BytesIO=None):
    cfg = ctx.Config()
    topic_id = cfg.get('topic_id')
    cost_anomaly(topic_id)
