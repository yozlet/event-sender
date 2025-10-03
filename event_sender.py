#!/usr/bin/env python3
"""
OpenTelemetry Event Sender for Honeycomb
Generates realistic web application metrics with Americas-based traffic patterns
"""

import os
import time
import random
import math
from datetime import datetime, timedelta, timezone
from typing import Dict

try:
    from dotenv import load_dotenv
    _ = load_dotenv()  # Load environment variables from .env file
except ImportError:
    pass  # dotenv is optional - continue without it

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
import requests


class WebAppMetricsGenerator:
    """Generates realistic web application metrics"""

    def __init__(self, honeycomb_api_key: str, dataset: str = "web-app-metrics"):
        self.honeycomb_api_key = honeycomb_api_key
        self.dataset = dataset

        # Configure OpenTelemetry
        self._setup_otel()

        # Web app configuration
        self.services = ["web-frontend", "api-gateway", "user-service", "order-service", "payment-service"]
        self.endpoints = {
            "web-frontend": ["/", "/login", "/signup", "/dashboard", "/profile", "/search"],
            "api-gateway": ["/api/v1/health", "/api/v1/auth", "/api/v1/users", "/api/v1/orders"],
            "user-service": ["/users", "/users/profile", "/users/preferences", "/auth/login"],
            "order-service": ["/orders", "/orders/history", "/orders/create", "/orders/cancel"],
            "payment-service": ["/payments", "/payments/process", "/payments/refund"]
        }
        self.regions = ["us-east-1", "us-west-2", "ca-central-1", "sa-east-1"]
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15",
            "Mozilla/5.0 (Android 11; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0"
        ]

        # Metrics
        self.request_duration_histogram = self.meter.create_histogram(
            name="http_request_duration_seconds",
            description="HTTP request duration in seconds",
            unit="s"
        )

        self.request_counter = self.meter.create_counter(
            name="http_requests_total",
            description="Total HTTP requests"
        )

        self.active_users_gauge = self.meter.create_up_down_counter(
            name="active_users",
            description="Number of active users"
        )

        self.error_counter = self.meter.create_counter(
            name="http_errors_total",
            description="Total HTTP errors"
        )

        self.db_query_duration = self.meter.create_histogram(
            name="db_query_duration_seconds",
            description="Database query duration in seconds",
            unit="s"
        )

        self.memory_usage_gauge = self.meter.create_up_down_counter(
            name="memory_usage_bytes",
            description="Memory usage in bytes"
        )

    def _setup_otel(self):
        """Configure OpenTelemetry for metric collection"""
        # Create resource with service information
        resource = Resource.create({
            "service.name": "event-sender",
            "service.version": "1.0.0",
            "deployment.environment": "production"
        })

        # Set up the meter provider (used for metric definitions, not actual recording)
        metrics.set_meter_provider(MeterProvider(resource=resource))
        self.meter = metrics.get_meter("web-app-metrics")

        # Store metric data points with custom timestamps
        self.metric_data_points = []

    def _record_metric_with_timestamp(self, metric_name: str, value: float, labels: Dict[str, str],
                                    timestamp: datetime, metric_type: str = "histogram"):
        """Record a metric data point with a specific timestamp"""
        timestamp_ns = int(timestamp.timestamp() * 1_000_000_000)  # Convert to nanoseconds

        data_point = {
            "name": metric_name,
            "value": value,
            "labels": labels,
            "timestamp_ns": timestamp_ns,
            "type": metric_type
        }

        self.metric_data_points.append(data_point)

    def get_traffic_multiplier(self, dt: datetime) -> float:
        """Calculate traffic multiplier based on time patterns"""
        # Americas timezone (EST/EDT)
        est_hour = (dt.hour - 5) % 24  # Rough EST conversion

        # Weekly pattern - lower traffic on weekends
        weekday_multiplier = 0.6 if dt.weekday() >= 5 else 1.0

        # Daily pattern - higher traffic during business hours
        if 6 <= est_hour <= 23:  # 6 AM to 11 PM EST
            # Peak hours: 9-12 AM, 2-5 PM, 7-9 PM
            if 9 <= est_hour <= 12 or 14 <= est_hour <= 17 or 19 <= est_hour <= 21:
                hour_multiplier = 1.5 + 0.3 * math.sin((est_hour - 9) * math.pi / 12)
            else:
                hour_multiplier = 1.0 + 0.2 * math.sin((est_hour - 6) * math.pi / 17)
        else:
            # Overnight hours
            hour_multiplier = 0.2 + 0.1 * random.random()

        return weekday_multiplier * hour_multiplier

    def generate_request_metrics(self, timestamp: datetime):
        """Generate HTTP request metrics"""
        traffic_mult = self.get_traffic_multiplier(timestamp)
        base_requests_per_minute = 1000
        requests_this_minute = int(base_requests_per_minute * traffic_mult * (0.8 + 0.4 * random.random()))

        for _ in range(requests_this_minute):
            service = random.choice(self.services)
            endpoint = random.choice(self.endpoints[service])
            method = random.choices(["GET", "POST", "PUT", "DELETE"], weights=[70, 20, 8, 2])[0]
            region = random.choices(self.regions, weights=[40, 30, 20, 10])[0]
            user_agent = random.choice(self.user_agents)

            # Status code distribution
            status_code = random.choices(
                [200, 201, 400, 401, 403, 404, 500, 502, 503],
                weights=[80, 5, 3, 2, 1, 4, 2, 1, 2]
            )[0]

            # Response time based on endpoint and status
            if status_code >= 500:
                duration = random.lognormvariate(1.5, 0.8)  # Slower for errors
            elif endpoint in ["/", "/health"]:
                duration = random.lognormvariate(-1, 0.5)  # Fast for simple endpoints
            else:
                duration = random.lognormvariate(0, 0.7)   # Normal distribution

            duration = max(0.001, min(30.0, duration))  # Clamp between 1ms and 30s

            labels = {
                "service": service,
                "endpoint": endpoint,
                "method": method,
                "status_code": str(status_code),
                "region": region,
                "user_agent_type": self._classify_user_agent(user_agent)
            }

            # Record metrics with historical timestamp
            self._record_metric_with_timestamp("http_request_duration_seconds", duration, labels, timestamp, "histogram")
            self._record_metric_with_timestamp("http_requests_total", 1, labels, timestamp, "counter")

            if status_code >= 400:
                self._record_metric_with_timestamp("http_errors_total", 1, labels, timestamp, "counter")

    def generate_database_metrics(self, timestamp: datetime):
        """Generate database query metrics"""
        traffic_mult = self.get_traffic_multiplier(timestamp)
        base_queries_per_minute = 500
        queries_this_minute = int(base_queries_per_minute * traffic_mult * (0.9 + 0.2 * random.random()))

        query_types = ["SELECT", "INSERT", "UPDATE", "DELETE"]
        tables = ["users", "orders", "products", "sessions", "analytics"]

        for _ in range(queries_this_minute):
            query_type = random.choices(query_types, weights=[70, 15, 10, 5])[0]
            table = random.choice(tables)

            # Query duration based on type and complexity
            if query_type == "SELECT":
                duration = random.lognormvariate(-2, 0.6)  # Fast selects
            elif query_type == "INSERT":
                duration = random.lognormvariate(-1.5, 0.4)  # Fast inserts
            else:
                duration = random.lognormvariate(-1, 0.8)   # Slower updates/deletes

            duration = max(0.001, min(10.0, duration))

            labels = {
                "query_type": query_type,
                "table": table,
                "service": random.choice(self.services[1:])  # Skip frontend
            }

            self._record_metric_with_timestamp("db_query_duration_seconds", duration, labels, timestamp, "histogram")

    def generate_system_metrics(self, timestamp: datetime):
        """Generate system resource metrics"""
        for service in self.services:
            # Memory usage with some realistic variation
            base_memory = {
                "web-frontend": 512 * 1024 * 1024,  # 512MB
                "api-gateway": 256 * 1024 * 1024,   # 256MB
                "user-service": 384 * 1024 * 1024,  # 384MB
                "order-service": 512 * 1024 * 1024, # 512MB
                "payment-service": 256 * 1024 * 1024 # 256MB
            }

            traffic_mult = self.get_traffic_multiplier(timestamp)
            memory_usage = int(base_memory[service] * (0.8 + 0.4 * traffic_mult + 0.1 * random.random()))

            labels = {"service": service}
            self._record_metric_with_timestamp("memory_usage_bytes", memory_usage, labels, timestamp, "gauge")

    def generate_user_metrics(self, timestamp: datetime):
        """Generate active user metrics"""
        traffic_mult = self.get_traffic_multiplier(timestamp)
        base_active_users = 5000
        active_users = int(base_active_users * traffic_mult * (0.9 + 0.2 * random.random()))

        # Distribute across regions
        for region in self.regions:
            region_weight = {"us-east-1": 0.4, "us-west-2": 0.3, "ca-central-1": 0.2, "sa-east-1": 0.1}
            region_users = int(active_users * region_weight[region])

            labels = {"region": region}
            self._record_metric_with_timestamp("active_users", region_users, labels, timestamp, "gauge")

    def _export_collected_metrics(self):
        """Export all collected metrics with their historical timestamps to Honeycomb"""
        if not self.metric_data_points:
            return

        print(f"Exporting {len(self.metric_data_points)} metric data points...")

        # Convert metric data points to Honeycomb events format
        events = []
        for data_point in self.metric_data_points:
            # Convert nanoseconds timestamp to ISO string
            timestamp_dt = datetime.fromtimestamp(data_point["timestamp_ns"] / 1_000_000_000, tz=timezone.utc)

            # Create event in Honeycomb format
            event = {
                "time": timestamp_dt.isoformat(),
                "data": {
                    "metric_name": data_point["name"],
                    "value": data_point["value"],
                    "metric_type": data_point["type"],
                    **data_point["labels"]  # Spread labels as individual fields
                }
            }
            events.append(event)

        # Send events in batches to Honeycomb
        batch_size = 100  # Honeycomb recommends smaller batches for events
        total_events = len(events)
        successful_batches = 0

        for i in range(0, total_events, batch_size):
            batch = events[i:i+batch_size]

            try:
                # Send to Honeycomb Events API
                response = requests.post(
                    f"https://api.honeycomb.io/1/batch/{self.dataset}",
                    headers={
                        "X-Honeycomb-Team": self.honeycomb_api_key,
                        "Content-Type": "application/json"
                    },
                    json=batch,
                    timeout=30
                )

                if response.status_code == 200:
                    successful_batches += 1
                    print(f"✓ Exported batch {i//batch_size + 1}/{(total_events-1)//batch_size + 1}: {len(batch)} events")
                else:
                    print(f"✗ Failed to export batch {i//batch_size + 1}: HTTP {response.status_code} - {response.text}")

            except requests.exceptions.RequestException as e:
                print(f"✗ Failed to export batch {i//batch_size + 1}: {e}")

            # Small delay between batches
            time.sleep(0.1)

        # Clear the collected data points
        self.metric_data_points.clear()
        print(f"Export completed: {successful_batches}/{(total_events-1)//batch_size + 1} batches successful")

    def _classify_user_agent(self, user_agent: str) -> str:
        """Classify user agent into categories"""
        if "iPhone" in user_agent or "Android" in user_agent:
            return "mobile"
        elif "Windows" in user_agent or "Macintosh" in user_agent:
            return "desktop"
        else:
            return "other"

    def generate_metrics_for_timerange(self, start_date: datetime, end_date: datetime,
                                     interval_minutes: int = 1):
        """Generate metrics for a specific time range"""
        current_time = start_date
        total_intervals = int((end_date - start_date).total_seconds() / (interval_minutes * 60))

        print(f"Generating metrics from {start_date} to {end_date}")
        print(f"Total intervals: {total_intervals} ({interval_minutes} minute intervals)")

        interval_count = 0
        while current_time < end_date:
            # Generate all metric types for this time interval
            self.generate_request_metrics(current_time)
            self.generate_database_metrics(current_time)
            self.generate_system_metrics(current_time)
            self.generate_user_metrics(current_time)

            # Progress reporting and periodic export
            interval_count += 1
            if interval_count % 100 == 0:
                progress = (interval_count / total_intervals) * 100
                print(f"Progress: {progress:.1f}% ({interval_count}/{total_intervals})")
                # Export metrics periodically to avoid memory buildup
                self._export_collected_metrics()

            current_time += timedelta(minutes=interval_minutes)

            # Small delay to prevent overwhelming the system
            time.sleep(0.01)

    def run_historical_generation(self, days: int = 35):
        """Generate historical metrics for the specified number of days"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)

        print(f"Starting historical metrics generation for {days} days")
        print(f"Time range: {start_time} to {end_time}")

        self.generate_metrics_for_timerange(start_time, end_time)

        # Export any remaining metrics
        self._export_collected_metrics()
        print("Historical metrics generation completed!")

    def run_realtime_generation(self, duration_hours: int = 1):
        """Generate real-time metrics for testing"""
        print(f"Starting real-time metrics generation for {duration_hours} hours")

        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)

        while time.time() < end_time:
            current_dt = datetime.now(timezone.utc)

            self.generate_request_metrics(current_dt)
            self.generate_database_metrics(current_dt)
            self.generate_system_metrics(current_dt)
            self.generate_user_metrics(current_dt)

            print(f"Generated metrics batch at {current_dt.strftime('%H:%M:%S')}")
            time.sleep(60)  # Generate every minute

        print("Real-time metrics generation completed!")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate OpenTelemetry metrics for Honeycomb")
    parser.add_argument("--api-key", help="Honeycomb API key (defaults to HONEYCOMB_API_KEY env var)")
    parser.add_argument("--dataset", default="web-app-metrics", help="Honeycomb dataset name")
    parser.add_argument("--days", type=int, default=35, help="Days of historical data to generate")
    parser.add_argument("--realtime", type=int, help="Generate real-time data for N hours instead")

    args = parser.parse_args()

    # Get API key from command line or environment variable
    api_key = args.api_key or os.getenv("HONEYCOMB_API_KEY")
    if not api_key:
        print("Error: Honeycomb API key required. Provide via --api-key or set HONEYCOMB_API_KEY environment variable.")
        return

    generator = WebAppMetricsGenerator(api_key, args.dataset)

    if args.realtime:
        generator.run_realtime_generation(args.realtime)
    else:
        generator.run_historical_generation(args.days)


if __name__ == "__main__":
    main()
