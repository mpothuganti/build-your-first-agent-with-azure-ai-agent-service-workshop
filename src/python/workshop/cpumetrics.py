import aiosqlite
import boto3
import json
from datetime import datetime, timedelta, timezone
from azure.ai.agents.models import FunctionTool
from typing import Optional

class CpuMetrics:
    def __init__(self: "CpuMetrics") -> None:
        self.conn: Optional[aiosqlite.Connection] = None
        
    # 1. Function to fetch CPU usage from CloudWatch
    def get_cpu_usage(instance_id: str, region: str = "us-east-1", period_hours: int = 168) -> str:
        """
        Fetch the average CPU utilization for the given EC2 instance over a time period.

        :param instance_id: The EC2 instance ID to query (e.g., i-0abcd1234ef567890).
        :param region: AWS region of the instance (e.g., us-east-1). default to us-east-1.
        :param period_hours: Number of hours to look back for the average (default 168h = 7 days).
        :return: JSON string: { "instance_id": ..., "avg_cpu": ..., "period_hours": ... }
        :rtype: str
        """
        cw = boto3.client("cloudwatch", aws_access_key_id= "", aws_secret_access_key="", region_name=region)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=period_hours)

        resp = cw.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,  # 1-hour buckets
            Statistics=["Average"]
        )
        datapoints = resp.get("Datapoints", [])
        if not datapoints:
            result = {
                "instance_id": instance_id,
                "avg_cpu": None,
                "period_hours": period_hours,
                "message": "No datapoints available"
            }
        else:
            avg = sum(dp["Average"] for dp in datapoints) / len(datapoints)
            result = {
                "instance_id": instance_id,
                "avg_cpu": round(avg, 2),
                "period_hours": period_hours
            }
        return json.dumps(result)


