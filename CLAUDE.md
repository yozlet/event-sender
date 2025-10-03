# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based OpenTelemetry event generator that creates realistic web application metrics and sends them to Honeycomb with historical timestamps. The main use case is backfilling weeks or months of historical observability data.

## Key Commands

### Setup
```bash
uv sync                           # Install dependencies (recommended)
pip install -e .                  # Alternative installation method
```

### Running the Generator

Generate historical data (default 35 days):
```bash
python event_sender.py --api-key YOUR_KEY
```

Generate custom time range:
```bash
python event_sender.py --api-key YOUR_KEY --days 60
```

Generate real-time metrics (for testing):
```bash
python event_sender.py --api-key YOUR_KEY --realtime 2
```

Use custom dataset:
```bash
python event_sender.py --api-key YOUR_KEY --dataset my-custom-dataset
```

### Testing
```bash
python test_historical_timestamps.py    # Verify timestamp functionality
python example.py                       # Run example scenarios
```

## Architecture

### Core Components

**event_sender.py** - Main module containing `WebAppMetricsGenerator` class
- Uses OpenTelemetry SDK for metric definitions (not for export)
- Custom timestamp handling: Metrics are stored in-memory with nanosecond timestamps
- Exports directly to Honeycomb Events API using requests library
- Does NOT use standard OTLP exporters (they don't support historical timestamps)

### Key Design Patterns

**Historical Timestamp Implementation**:
- `_record_metric_with_timestamp()` stores metrics with custom timestamps in `self.metric_data_points`
- `_export_collected_metrics()` converts stored metrics to Honeycomb event format and sends via batch API
- Timestamps converted to nanoseconds and stored with each data point
- Metrics exported in batches of 100 to avoid memory buildup

**Traffic Pattern Simulation**:
- `get_traffic_multiplier()` creates realistic Americas-based patterns
- Higher traffic during EST business hours (9-12 AM, 2-5 PM, 7-9 PM)
- Reduced weekend traffic (60% of weekday)
- Overnight traffic significantly reduced (20% of peak)
- Geographic distribution weighted toward US regions

**Metric Generation**:
- Five separate metric generators: requests, database, system, user metrics
- Each generator called per time interval (default 1 minute)
- Uses log-normal distributions for realistic response times
- Status codes and error rates based on weighted random selection

### Configuration

**Environment Variables**:
- `HONEYCOMB_API_KEY` - API key (loaded via python-dotenv if .env file exists)
- Command-line args override environment variables

**Simulated Services**:
- web-frontend, api-gateway, user-service, order-service, payment-service
- Each service has specific endpoints defined in `self.endpoints` dict

**Generated Metrics**:
- `http_request_duration_seconds` (histogram)
- `http_requests_total` (counter)
- `http_errors_total` (counter)
- `db_query_duration_seconds` (histogram)
- `active_users` (gauge/up-down counter)
- `memory_usage_bytes` (gauge/up-down counter)

## Important Implementation Notes

- When modifying metric generation, maintain historical timestamp support via `_record_metric_with_timestamp()`
- Batch size is 100 events per request to Honeycomb - changing this may impact API rate limits
- Progress export happens every 100 time intervals to prevent memory issues on long runs
- All timestamps are UTC timezone-aware datetime objects
- API endpoint is `https://api.honeycomb.io/1/batch/{dataset}` using Events API format
