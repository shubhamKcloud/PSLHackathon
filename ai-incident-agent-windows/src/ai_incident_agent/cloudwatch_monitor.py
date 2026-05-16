from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CloudWatchMonitor:
    """Monitor AWS CloudWatch log groups for error logs."""

    def __init__(
        self,
        log_group_name: str,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_region: str = "us-east-1",
    ) -> None:
        """
        Initialize CloudWatch monitor.

        Args:
            log_group_name: Name of the CloudWatch log group to monitor
            aws_access_key_id: AWS access key
            aws_secret_access_key: AWS secret key
            aws_region: AWS region name
        """
        self.log_group_name = log_group_name
        self.aws_region = aws_region
        self._last_check: datetime = datetime.now(timezone.utc) - timedelta(minutes=5)

        try:
            self.client = boto3.client(
                "logs",
                region_name=aws_region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
            # Verify connection
            self.client.describe_log_groups(logGroupNamePrefix=log_group_name, limit=1)
            logger.info(f"Connected to CloudWatch log group: {log_group_name}")
            print(f"[CLOUDWATCH] ✓ Connected to: {log_group_name}")
        except ClientError as e:
            error_msg = f"Failed to connect to CloudWatch: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def collect(self) -> list[dict[str, Any]]:
        """
        Collect new error/critical log events from CloudWatch.

        Returns:
            List of normalized log events
        """
        events: list[dict[str, Any]] = []

        try:
            # Query for error/critical logs since last check
            query = self._build_query()
            
            response = self.client.start_query(
                logGroupName=self.log_group_name,
                startTime=int(self._last_check.timestamp()),
                endTime=int(datetime.now(timezone.utc).timestamp()),
                queryString=query,
            )

            query_id = response["queryId"]

            # Wait for query to complete
            import time
            max_wait = 30
            elapsed = 0
            while elapsed < max_wait:
                result = self.client.get_query_results(queryId=query_id)
                if result["status"] == "Complete":
                    break
                time.sleep(1)
                elapsed += 1

            if result["status"] != "Complete":
                logger.warning(f"CloudWatch query timeout for {self.log_group_name}")
                return events

            # Parse results
            for record in result["results"]:
                event = self._parse_log_record(record)
                if event:
                    events.append(event)

            if events:
                logger.info(f"Collected {len(events)} new error events from CloudWatch")

        except ClientError as e:
            logger.error(f"Error querying CloudWatch: {e}")

        # Update last check time
        self._last_check = datetime.now(timezone.utc)
        return events

    def _build_query(self) -> str:
        """Build CloudWatch Insights query for error/critical logs."""
        return "fields @timestamp, @message, @logStream | filter @message like /error|critical|fail|exception/i"

    def _parse_log_record(self, record: list[dict[str, str]]) -> dict[str, Any] | None:
        """
        Parse a CloudWatch Insights query result.

        Args:
            record: Query result record (list of field dicts)

        Returns:
            Normalized log event dict
        """
        if not record:
            return None

        fields = {field["field"]: field["value"] for field in record}
        message = fields.get("@message", "")
        
        if not message:
            return None

        # Normalize log level
        normalized = message.lower()
        if "critical" in normalized or "fatal" in normalized:
            level = "critical"
        elif "error" in normalized:
            level = "error"
        else:
            level = "unknown"

        return {
            "raw_line": message,
            "level": level,
            "source": fields.get("@logStream", "cloudwatch"),
            "message": message,
            "path": f"cloudwatch://{self.log_group_name}",
            "timestamp": fields.get("@timestamp", ""),
        }

