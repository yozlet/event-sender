#!/usr/bin/env python3
"""
Test script to verify historical timestamp functionality
"""

from event_sender import WebAppMetricsGenerator
from datetime import datetime, timezone, timedelta
import os

def test_historical_timestamps():
    """Test that metrics are generated with correct historical timestamps"""

    # Create a generator (with dummy API key for testing)
    generator = WebAppMetricsGenerator("test-api-key", "test-dataset")

    # Generate metrics for a small time window
    start_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    end_time = start_time + timedelta(minutes=5)

    print(f"Testing historical timestamp generation...")
    print(f"Time window: {start_time} to {end_time}")

    # Generate some test metrics
    generator.generate_request_metrics(start_time)
    generator.generate_database_metrics(start_time + timedelta(minutes=1))
    generator.generate_system_metrics(start_time + timedelta(minutes=2))
    generator.generate_user_metrics(start_time + timedelta(minutes=3))

    print(f"Generated {len(generator.metric_data_points)} metric data points")

    # Check that timestamps are correct
    if generator.metric_data_points:
        first_point = generator.metric_data_points[0]
        timestamp_dt = datetime.fromtimestamp(first_point["timestamp_ns"] / 1_000_000_000, tz=timezone.utc)
        print(f"First metric timestamp: {timestamp_dt}")
        print(f"Expected around: {start_time}")

        # Verify timestamp is in expected range
        time_diff = abs((timestamp_dt - start_time).total_seconds())
        if time_diff < 300:  # Within 5 minutes
            print("✓ Historical timestamp test PASSED")
        else:
            print(f"✗ Historical timestamp test FAILED - time difference: {time_diff} seconds")

    # Test the export method (won't actually send without real API key)
    print("\nTesting export method structure...")
    try:
        # This will fail HTTP request but should process the data structure correctly
        generator._export_collected_metrics()
        print("✓ Export method structure test PASSED")
    except Exception as e:
        print(f"✗ Export method test FAILED: {e}")

if __name__ == "__main__":
    test_historical_timestamps()
