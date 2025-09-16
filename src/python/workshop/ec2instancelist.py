import json
from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.ai.agents.models import FunctionTool
from typing import Optional, List

class Ec2InstanceList:
    def __init__(self: "Ec2InstanceList") -> None:
        self.credential = DefaultAzureCredential()
        self.client = ResourceGraphClient(self.credential)

    def get_ec2_instance_inventory(self, 
                                   subscriptions: Optional[List[str]] = ["1c70e365-4937-4ff9-8524-262064a268d8"]) -> str:
        """
        Fetch all EC2 instance inventory using Azure Resource Graph query.

        :param subscriptions: List of Azure subscription IDs to query
        :return: JSON string of EC2 instance inventory
        :rtype: str
        """
        from azure.mgmt.resourcegraph.models import QueryRequest
        query = "awsresources | where type == 'microsoft.awsconnector/ec2instances'"
        request = QueryRequest(
            subscriptions=subscriptions,
            query=query,
            options={"result_format": "table"}
        )
        response = self.client.resources(request)
        return json.dumps(response.data)
