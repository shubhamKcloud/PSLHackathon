from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .analyzer import Analyzer
from .log_monitor import LogMonitor
from .cloudwatch_monitor import CloudWatchMonitor
from .remediator import Remediator
from .ticketing import Ticketing

class AIAgent:
    def __init__(
        self,
        log_sources: list[str],
        ticketing_config: dict[str, Any],
        model_client: Any,
        knowledge_base_dir: str | Path | None = None,
        cloudwatch_config: dict[str, Any] | None = None,
    ) -> None:
        self.monitor = LogMonitor(log_sources)
        self.cloudwatch_monitor = None
        
        # Initialize CloudWatch monitor if configured
        if cloudwatch_config and cloudwatch_config.get("enabled"):
            try:
                self.cloudwatch_monitor = CloudWatchMonitor(
                    log_group_name=cloudwatch_config.get("log_group"),
                    aws_access_key_id=cloudwatch_config.get("aws_access_key_id"),
                    aws_secret_access_key=cloudwatch_config.get("aws_secret_access_key"),
                    aws_region=cloudwatch_config.get("aws_region", "us-east-1"),
                )
                print(f"[AGENT] CloudWatch monitor enabled for: {cloudwatch_config.get('log_group')}")
            except Exception as e:
                print(f"[AGENT] Warning: CloudWatch not available: {e}")
        
        self.analyzer = Analyzer(model_client, knowledge_base_dir=knowledge_base_dir)
        self.ticketing = Ticketing(ticketing_config.get("provider", "file"), ticketing_config)
        self.remediator = Remediator(model_client)

    def run_cycle(self) -> dict[str, Any]:
        """Collect logs from all sources and process anomalies."""
        logs: list[dict[str, Any]] = []
        
        # Collect from local logs
        logs.extend(self.monitor.collect())
        
        # Collect from CloudWatch if enabled
        if self.cloudwatch_monitor:
            try:
                logs.extend(self.cloudwatch_monitor.collect())
            except Exception as e:
                print(f"[AGENT] Error collecting CloudWatch logs: {e}")
        
        # Detect anomalies using the same filter
        anomalies = self.monitor.detect_anomalies(logs)
        
        if anomalies:
            print(f"\n[CYCLE] Found {len(anomalies)} anomaly(ies)")
        
        incident_reports = []

        for i, anomaly in enumerate(anomalies):
            print(f"  [{i+1}] Processing: {anomaly.get('message', 'unknown')[:60]}...")
            analysis = self.analyzer.root_cause(anomaly)
            print(f"      ✓ Analysis complete: {analysis.get('summary', '')[:50]}...")
            if analysis.get('source') == 'knowledge_base':
                print(f"      ✓ Matched KB entry: {analysis.get('knowledge_base_entry', 'unknown')}")
            else:
                print(f"      ✓ Analysis source: {analysis.get('source', 'AI')}")

            incident_description = analysis.get("knowledge_base", {}).get("error_description") or analysis.get("summary")
            incident_root_cause = analysis.get("knowledge_base", {}).get("root_cause") or analysis.get("summary")
            incident_resolution = analysis.get("knowledge_base", {}).get("resolution") or analysis.get("recommendation")
            incident_owner = analysis.get("knowledge_base", {}).get("owner") or ("AI" if analysis.get("source") != "knowledge_base" else "Unknown")

            incident = {
                "title": f"Auto-detected issue: {anomaly.get('source', 'unknown')}",
                "description": incident_description,
                "severity": anomaly.get("severity", "P2"),
                "root_cause": incident_root_cause,
                "analysis_source": analysis.get("source", "ai"),
                "resolution": incident_resolution,
                "owner": incident_owner,
                "analysis": analysis,
                "raw": anomaly,
            }
            ticket = self.ticketing.create_ticket(incident)
            print(f"      ✓ Ticket created: {ticket['id']}")
            
            remediation = self.remediator.generate_fix(incident)
            print(f"      ✓ Remediation generated: {remediation.get('fix_summary', '')[:50]}...")
            
            incident_reports.append({
                "anomaly": anomaly,
                "ticket": ticket,
                "remediation": remediation,
            })

        return {"incidents": incident_reports}

    def run_forever(self, interval: float = 5.0) -> None:
        """Run continuous monitoring loop."""
        print(f"Starting continuous monitoring for {self.monitor.sources}")
        if self.cloudwatch_monitor:
            print(f"  + CloudWatch log group: {self.cloudwatch_monitor.log_group_name}")
        try:
            while True:
                result = self.run_cycle()
                if result["incidents"]:
                    print(f"Created {len(result['incidents'])} incident(s)")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("Monitoring stopped by user.")
