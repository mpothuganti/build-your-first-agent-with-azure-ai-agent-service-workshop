import json
from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.ai.agents.models import FunctionTool
from typing import Optional, List
from azure.mgmt.resourcegraph.models import QueryRequest
from azure.mgmt.resourcegraph.models import QueryRequest

class Ec2InstanceList:
    def __init__(self: "Ec2InstanceList") -> None:
        self.credential = DefaultAzureCredential()
        self.client = ResourceGraphClient(self.credential)

    def get_ec2_instance_inventory(self, 
                                   connectorName: str,
                                   subscriptions: Optional[List[str]] = ["1c70e365-4937-4ff9-8524-262064a268d8"]) -> str:
        """
        Fetch all EC2 instance inventory using Azure Resource Graph query.

        : param connectorName: The name of the AWS connector resource in Azure.
        :param subscriptions: List of Azure subscription IDs to query
        :return: JSON string of EC2 instance inventory
        :rtype: str
        """
        query = (
            "awsresources "
            "| where type == 'microsoft.awsconnector/ec2instances' "
            "| where properties.publicCloudConnectorsResourceId contains '" + connectorName + "' "
            "| where resourceGroup contains '730335494975' "
            "| project instanceId=properties.awsProperties.instanceId, "
            "instanceType=properties.awsProperties.instanceType.value, "
            "launchTime=properties.awsProperties.launchTime, "
            "status=properties.awsProperties.state.name.value, "
            "region=properties.awsRegion "
        )
        
        all_instances = []
        skip_token = None
        while True:
            request = QueryRequest(
                subscriptions=subscriptions,
                query=query,
                options={"result_format": "table"},
                skip_token=skip_token
            )
            response = self.client.resources(request)
            data = response.data.get('rows', []) if hasattr(response.data, 'get') else response.data['rows']
            all_instances.extend(data)
            skip_token = getattr(response, 'skip_token', None)
            if not skip_token:
                break
        return json.dumps({"rows": all_instances})
