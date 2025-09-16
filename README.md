# Event Sender for Honeycomb

A Python script that generates realistic web application events and sends them to Honeycomb with proper historical timestamps.

## Features

- **Historical timestamps** - Events have actual historical dates, not current time
- Generates realistic web app metrics (HTTP requests, database queries, system resources, active users)
- Americas-based traffic patterns with higher weekday activity
- Configurable time ranges (can generate months of historical data)
- Multiple microservices simulation
- Realistic response time distributions
- Error rate simulation
- **.env file support** for API keys

## Installation

1. Install dependencies using uv:
```bash
uv sync
```

Or alternatively with pip:
```bash
pip install -e .

## Usage

### Historical Data Generation (Default)

Generate 35 days of historical metrics:
```bash
python event_sender.py --api-key YOUR_HONEYCOMB_API_KEY
```

Generate custom time range:
```bash
python event_sender.py --api-key YOUR_HONEYCOMB_API_KEY --days 60
```

### Real-time Data Generation

Generate real-time metrics for testing:
```bash
python event_sender.py --api-key YOUR_HONEYCOMB_API_KEY --realtime 2
```

### Custom Dataset

Specify a custom Honeycomb dataset:
```bash
python event_sender.py --api-key YOUR_HONEYCOMB_API_KEY --dataset my-custom-dataset
```

## Metrics Generated

- **HTTP Request Duration** - Histogram of request response times
- **HTTP Request Count** - Counter of total requests by service/endpoint
- **HTTP Errors** - Counter of 4xx/5xx responses
- **Database Query Duration** - Histogram of DB query times
- **Active Users** - Gauge of concurrent users by region
- **Memory Usage** - Gauge of service memory consumption

## Traffic Patterns

- **Geographic**: Weighted toward US regions (us-east-1: 40%, us-west-2: 30%, ca-central-1: 20%, sa-east-1: 10%)
- **Temporal**: Higher traffic during EST business hours, reduced weekend activity
- **Peak Hours**: 9-12 AM, 2-5 PM, 7-9 PM EST
- **Overnight**: Significantly reduced traffic

## Services Simulated

- web-frontend
- api-gateway  
- user-service
- order-service
- payment-service