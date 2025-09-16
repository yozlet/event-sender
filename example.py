#!/usr/bin/env python3
"""
Example usage of the WebApp Metrics Generator
"""

from event_sender import WebAppMetricsGenerator
from datetime import datetime, timezone, timedelta
import os

def main():
    # Get API key from environment or replace with your actual key
    api_key = os.getenv("HONEYCOMB_API_KEY", "your-api-key-here")

    if api_key == "your-api-key-here":
        print("Please set HONEYCOMB_API_KEY environment variable or update the api_key in this script")
        return

    # Create the generator
    generator = WebAppMetricsGenerator(api_key, "example-web-app")

    # Example 1: Generate 7 days of historical data
    print("Generating 7 days of historical data...")
    generator.run_historical_generation(days=7)

    # Example 2: Generate specific time range
    print("\nGenerating specific time range...")
    start_time = datetime.now(timezone.utc) - timedelta(days=2)
    end_time = datetime.now(timezone.utc) - timedelta(days=1)
    generator.generate_metrics_for_timerange(start_time, end_time, interval_minutes=5)

    print("\nExample completed!")

if __name__ == "__main__":
    main()
