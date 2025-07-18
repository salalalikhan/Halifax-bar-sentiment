# Halifax Bar Sentiment Analysis API Documentation

## Overview

The Halifax Bar Sentiment Analysis API provides comprehensive sentiment analysis for Halifax bars mentioned in Reddit discussions. This professional-grade API offers advanced sentiment analysis, real-time monitoring, and detailed analytics.

## Version: 2.0.0

## Base URL
- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

## Authentication
Currently, the API is open access. Authentication will be added in future versions.

## API Endpoints

### Health & Status

#### GET `/health`
Get basic health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "database_connected": true,
  "last_data_update": "2023-06-20T14:30:00Z",
  "total_mentions": 5000
}
```

#### GET `/monitoring/health/detailed`
Get detailed health status including system metrics.

**Response:**
```json
{
  "overall_status": "healthy",
  "timestamp": "2023-06-20T14:30:00Z",
  "checks": {
    "database": {"status": "healthy"},
    "sentiment_models": {"status": "healthy"},
    "disk_space": {"status": "healthy"}
  },
  "system_metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 62.1,
    "disk_usage": 78.5
  }
}
```

### Bars

#### GET `/bars`
Get all bars with summary statistics.

**Parameters:**
- `limit` (optional): Maximum number of bars to return (1-100)

**Response:**
```json
[
  {
    "name": "Your Father's Moustache",
    "total_mentions": 464,
    "avg_sentiment": 0.12,
    "avg_confidence": 0.85,
    "positive_mentions": 200,
    "negative_mentions": 150,
    "neutral_mentions": 114,
    "first_mention": "2023-01-01T00:00:00Z",
    "last_mention": "2023-06-20T14:30:00Z",
    "top_emotions": {"joy": 0.7, "anger": 0.1},
    "specialties": ["wings", "beer", "atmosphere"]
  }
]
```

#### GET `/bars/{bar_name}`
Get detailed information about a specific bar.

**Parameters:**
- `bar_name`: Name of the bar (URL encoded)

**Response:**
```json
{
  "name": "Your Father's Moustache",
  "total_mentions": 464,
  "avg_sentiment": 0.12,
  "avg_confidence": 0.85,
  "positive_mentions": 200,
  "negative_mentions": 150,
  "neutral_mentions": 114,
  "first_mention": "2023-01-01T00:00:00Z",
  "last_mention": "2023-06-20T14:30:00Z",
  "top_emotions": {"joy": 0.7, "anger": 0.1},
  "specialties": ["wings", "beer", "atmosphere"]
}
```

#### GET `/bars/{bar_name}/mentions`
Get mentions for a specific bar.

**Parameters:**
- `bar_name`: Name of the bar (URL encoded)
- `limit` (optional): Maximum number of mentions (1-500, default: 50)
- `offset` (optional): Number of mentions to skip (default: 0)
- `start_date` (optional): Filter mentions after this date (ISO format)
- `end_date` (optional): Filter mentions before this date (ISO format)
- `sentiment` (optional): Filter by sentiment (`positive`, `negative`, `neutral`)

**Response:**
```json
[
  {
    "id": 1,
    "bar_name": "Your Father's Moustache",
    "post_id": "abc123",
    "post_title": "Great experience last night",
    "post_text": "Had amazing wings and beer...",
    "created_at": "2023-06-20T14:30:00Z",
    "sentiment_score": 0.8,
    "sentiment_confidence": 0.92,
    "sentiment_label": "positive",
    "model_scores": {
      "vader": 0.7,
      "textblob": 0.85,
      "roberta": 0.9
    },
    "emotion_scores": {
      "joy": 0.8,
      "anger": 0.1,
      "fear": 0.05
    },
    "food_mentions": ["wings", "beer"],
    "url": "https://reddit.com/r/halifax/comments/abc123",
    "is_comment": false
  }
]
```

### Mentions

#### GET `/mentions`
Get all mentions with optional filtering.

**Parameters:**
- `limit` (optional): Maximum number of mentions (1-500, default: 50)
- `offset` (optional): Number of mentions to skip (default: 0)
- `start_date` (optional): Filter mentions after this date (ISO format)
- `end_date` (optional): Filter mentions before this date (ISO format)
- `sentiment` (optional): Filter by sentiment (`positive`, `negative`, `neutral`)

**Response:** Same as `/bars/{bar_name}/mentions`

#### POST `/search`
Search mentions with full-text search.

**Request Body:**
```json
{
  "query": "great food",
  "bars": ["Your Father's Moustache", "The Bitter End"],
  "sentiment": "positive",
  "start_date": "2023-01-01T00:00:00Z",
  "end_date": "2023-06-20T23:59:59Z",
  "limit": 20
}
```

**Response:**
```json
{
  "query": "great food",
  "total_results": 45,
  "results": [
    // Array of MentionDetail objects
  ],
  "filters_applied": {
    "bars": ["Your Father's Moustache", "The Bitter End"],
    "sentiment": "positive",
    "start_date": "2023-01-01T00:00:00Z",
    "end_date": "2023-06-20T23:59:59Z",
    "limit": 20
  }
}
```

### Analytics

#### GET `/analytics/summary`
Get overall analytics summary.

**Response:**
```json
{
  "total_mentions": 5000,
  "unique_bars": 25,
  "avg_sentiment_score": 0.15,
  "sentiment_distribution": {
    "positive": 2000,
    "negative": 1500,
    "neutral": 1500
  },
  "top_bars": [
    {
      "name": "Your Father's Moustache",
      "mentions": 464,
      "sentiment": 0.12
    }
  ],
  "trending_foods": [
    {
      "food": "wings",
      "count": 800
    }
  ],
  "data_quality_score": 0.85,
  "analysis_date": "2023-06-20T14:30:00Z"
}
```

#### POST `/analytics/trends`
Get sentiment trends over time.

**Request Body:**
```json
{
  "bars": ["Your Father's Moustache", "The Bitter End"],
  "days": 30,
  "granularity": "daily"
}
```

**Response:**
```json
{
  "period_start": "2023-05-21T00:00:00Z",
  "period_end": "2023-06-20T23:59:59Z",
  "granularity": "daily",
  "trends": [
    {
      "date": "2023-06-20T00:00:00Z",
      "bar_name": "Your Father's Moustache",
      "mention_count": 15,
      "avg_sentiment": 0.2,
      "avg_confidence": 0.88,
      "positive_count": 8,
      "negative_count": 4,
      "neutral_count": 3
    }
  ],
  "summary_stats": {
    "total_mentions": 450,
    "average_sentiment": 0.15,
    "period_days": 30,
    "bars_analyzed": 2
  }
}
```

#### POST `/analytics/compare`
Compare multiple bars across different metrics.

**Request Body:**
```json
{
  "bars": ["Your Father's Moustache", "The Bitter End", "Good Robot"],
  "metrics": ["avg_sentiment", "total_mentions", "avg_confidence"],
  "days": 30
}
```

**Response:**
```json
{
  "bars": ["Your Father's Moustache", "The Bitter End", "Good Robot"],
  "metrics": ["avg_sentiment", "total_mentions", "avg_confidence"],
  "analysis_period": 30,
  "comparison_data": {
    "Your Father's Moustache": {
      "avg_sentiment": 0.15,
      "total_mentions": 120,
      "avg_confidence": 0.88
    },
    "The Bitter End": {
      "avg_sentiment": 0.08,
      "total_mentions": 95,
      "avg_confidence": 0.85
    },
    "Good Robot": {
      "avg_sentiment": 0.25,
      "total_mentions": 80,
      "avg_confidence": 0.90
    }
  },
  "rankings": {
    "avg_sentiment": ["Good Robot", "Your Father's Moustache", "The Bitter End"],
    "total_mentions": ["Your Father's Moustache", "The Bitter End", "Good Robot"]
  }
}
```

### Data Quality

#### GET `/quality/metrics`
Get recent data quality metrics.

**Parameters:**
- `limit` (optional): Maximum number of metrics to return (1-50, default: 10)

**Response:**
```json
[
  {
    "processing_date": "2023-06-20T14:30:00Z",
    "total_posts_processed": 1000,
    "valid_posts": 950,
    "invalid_posts": 50,
    "spam_filtered": 25,
    "mentions_found": 500,
    "unique_bars_mentioned": 20,
    "average_confidence": 0.85,
    "data_quality_score": 0.92
  }
]
```

### Processing

#### POST `/process`
Trigger background data processing job.

**Request Body:**
```json
{
  "limit": 1000,
  "mode": "advanced",
  "priority": "normal"
}
```

**Response:**
```json
{
  "job_id": "uuid-job-id",
  "status": "queued",
  "progress": 0
}
```

#### GET `/process/{job_id}`
Get status of a processing job.

**Response:**
```json
{
  "job_id": "uuid-job-id",
  "status": "completed",
  "progress": 100,
  "created_at": "2023-06-20T14:30:00Z",
  "started_at": "2023-06-20T14:30:05Z",
  "completed_at": "2023-06-20T14:32:30Z",
  "result_summary": {
    "posts_processed": 1000,
    "mentions_found": 500,
    "unique_bars": 20,
    "data_quality_score": 0.92
  }
}
```

### Monitoring

#### GET `/monitoring/metrics`
Get application performance metrics.

**Response:**
```json
{
  "timestamp": "2023-06-20T14:30:00Z",
  "posts_processed": 10000,
  "mentions_found": 5000,
  "data_quality_score": 0.85,
  "average_confidence": 0.88
}
```

#### GET `/monitoring/performance`
Get detailed performance metrics.

**Response:**
```json
{
  "timestamp": "2023-06-20T14:30:00Z",
  "cpu": {
    "usage_percent": 45.2,
    "usage_per_cpu": [40.1, 50.3, 45.0, 45.4],
    "cpu_count": 4
  },
  "memory": {
    "total": 8589934592,
    "available": 3221225472,
    "used": 5368709120,
    "percent": 62.5
  },
  "disk": {
    "total": 1000000000000,
    "used": 600000000000,
    "free": 400000000000,
    "percent": 60.0
  },
  "process": {
    "pid": 1234,
    "cpu_percent": 12.5,
    "memory_percent": 5.2,
    "num_threads": 15
  }
}
```

#### GET `/monitoring/alerts`
Get active system alerts.

**Response:**
```json
[
  {
    "type": "cpu_high",
    "severity": "warning",
    "message": "High CPU usage: 85.2%",
    "value": 85.2,
    "threshold": 80,
    "timestamp": "2023-06-20T14:30:00Z"
  }
]
```

#### GET `/monitoring/dashboard`
Get comprehensive monitoring dashboard data.

**Response:**
```json
{
  "timestamp": "2023-06-20T14:30:00Z",
  "summary": {
    "overall_health": "healthy",
    "active_alerts": 0,
    "total_errors": 5,
    "error_types": 2,
    "cpu_usage": 45.2,
    "memory_usage": 62.5,
    "disk_usage": 60.0
  },
  "health_status": {
    "overall_status": "healthy",
    "checks": {
      "database": {"status": "healthy"},
      "sentiment_models": {"status": "healthy"}
    }
  },
  "performance_metrics": {
    "posts_processed": 10000,
    "mentions_found": 5000
  },
  "error_summary": {
    "total_errors": 5,
    "error_types": 2
  },
  "system_metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 62.5,
    "disk_usage": 60.0
  },
  "alerts": []
}
```

## Error Handling

The API uses standard HTTP status codes and returns structured error responses:

```json
{
  "error": "Validation Error",
  "message": "Invalid request parameters",
  "details": {
    "field": "limit",
    "value": "invalid"
  }
}
```

### Common Status Codes
- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Rate Limiting

Currently, no rate limiting is implemented. This will be added in future versions.

## Data Models

### SentimentResult
- `score`: Float between -1 (negative) and 1 (positive)
- `confidence`: Float between 0 and 1
- `label`: String ('positive', 'negative', 'neutral')
- `model_scores`: Dictionary of individual model scores
- `emotion_scores`: Optional dictionary of emotion scores

### BarSummary
- `name`: String
- `total_mentions`: Integer
- `avg_sentiment`: Float
- `avg_confidence`: Float
- `positive_mentions`: Integer
- `negative_mentions`: Integer
- `neutral_mentions`: Integer
- `first_mention`: ISO timestamp
- `last_mention`: ISO timestamp
- `top_emotions`: Dictionary of emotion scores
- `specialties`: Array of strings

### MentionDetail
- `id`: Integer
- `bar_name`: String
- `post_id`: String
- `post_title`: String
- `post_text`: String
- `created_at`: ISO timestamp
- `sentiment_score`: Float
- `sentiment_confidence`: Float
- `sentiment_label`: String
- `model_scores`: Dictionary
- `emotion_scores`: Dictionary (optional)
- `food_mentions`: Array of strings
- `url`: String
- `is_comment`: Boolean

## SDK Usage Examples

### Python
```python
import requests

# Get health status
response = requests.get('http://localhost:8000/health')
health = response.json()

# Get top bars
response = requests.get('http://localhost:8000/bars?limit=10')
bars = response.json()

# Search mentions
search_data = {
    "query": "great food",
    "sentiment": "positive",
    "limit": 20
}
response = requests.post('http://localhost:8000/search', json=search_data)
results = response.json()
```

### JavaScript
```javascript
// Get analytics summary
fetch('http://localhost:8000/analytics/summary')
  .then(response => response.json())
  .then(data => console.log(data));

// Get sentiment trends
fetch('http://localhost:8000/analytics/trends', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    bars: ['Your Father\'s Moustache'],
    days: 30,
    granularity: 'daily'
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

### cURL
```bash
# Get health status
curl -X GET "http://localhost:8000/health"

# Get bar details
curl -X GET "http://localhost:8000/bars/Your%20Father's%20Moustache"

# Search mentions
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "great food", "limit": 10}'
```

## Support

For API support, please:
1. Check this documentation
2. Review the interactive API documentation at `/docs`
3. Submit issues on GitHub
4. Contact the development team

## Changelog

### v2.0.0
- Added advanced sentiment analysis with multiple models
- Implemented comprehensive monitoring and logging
- Added real-time dashboard capabilities
- Enhanced data quality validation
- Improved error handling and reporting