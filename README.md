# Halifax Bar Sentiment Analysis

This project analyzes sentiment and mentions of Halifax bars from Reddit discussions. It collects data from r/halifax, performs sentiment analysis, and stores the results in a PostgreSQL database.

## Features

### 🚀 Core Features
- **Advanced Sentiment Analysis**: Multi-model ensemble with VADER, RoBERTa, and TextBlob for accurate sentiment scoring
- **Real-time Dashboard**: Interactive React frontend with charts and analytics
- **Comprehensive API**: RESTful FastAPI backend with full documentation
- **Data Quality Management**: Automated validation, spam filtering, and quality scoring
- **Reddit Integration**: Automated data collection from r/halifax with comment processing

### 📊 Analytics & Insights
- **Sentiment Trends**: Track sentiment changes over time with customizable periods
- **Bar Comparisons**: Compare multiple bars across different metrics
- **Food & Drink Tracking**: Identify trending food and drink mentions
- **Geographic Analysis**: Halifax-specific bar sentiment mapping
- **Seasonal Patterns**: Detect seasonal trends and patterns

### 🔧 Technical Features
- **Monitoring & Logging**: Comprehensive structured logging with performance metrics
- **Health Checks**: Automated system health monitoring and alerting
- **Error Tracking**: Advanced error tracking with threshold-based alerts
- **Data Validation**: Robust data validation with Pydantic models
- **Background Processing**: Asynchronous job processing for large datasets

### 🛡️ Production Ready
- **Docker Support**: Full containerization with docker-compose
- **Database Optimization**: Indexed PostgreSQL with connection pooling
- **Caching**: Redis integration for improved performance
- **Security**: CORS, rate limiting, and security headers
- **Scalability**: Horizontal scaling support with load balancing

## Latest Analysis Results

### Top 5 Bars by Mentions
1. Your Father's Moustache (464 mentions, sentiment: 0.12)
2. The Bitter End (433 mentions, sentiment: 0.12)
3. Good Robot (279 mentions, sentiment: 0.29)
4. Gus' Pub (230 mentions, sentiment: 0.11)
5. HFX Sports Bar (173 mentions, sentiment: 0.16)

*Note: Sentiment scores range from -1 (very negative) to 1 (very positive), with 0 being neutral.*

## Setup Instructions

### Prerequisites
- Python 3.11+
- PostgreSQL
- Reddit API credentials

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/halifax_bar_sentiment.git
cd halifax_bar_sentiment
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
Copy the `env.example` file to `.env` and fill in your credentials:
```bash
cp env.example .env
```

5. Configure your `.env` file with:
```
# Reddit API credentials
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=Halifax Bar Analytics Tool

# PostgreSQL connection details
POSTGRES_DBNAME=halifaxbars
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

6. Create PostgreSQL database:
```bash
psql -U postgres -c "CREATE DATABASE halifaxbars;"
```

### Running the Project

Run the main script:
```bash
python main.py
```

## Project Structure
- `main.py`: Main orchestration script
- `extract.py`: Reddit data collection
- `transform.py`: Sentiment analysis and data processing
- `load.py`: Database operations
- `config.py`: Configuration management
- `constants.py`: Project constants

## Database Schema

### Mentions Table
- `id`: Primary key
- `bar_name`: Bar name (foreign key to bars table)
- `post_id`: Reddit post ID
- `post_title`: Post title
- `post_text`: Post content
- `created_at`: Post creation time
- `sentiment`: Sentiment score
- `food_mentions`: Array of food/drink mentions
- `url`: Reddit post URL
- `created_at_db`: Database entry timestamp

## Contributing
Feel free to open issues or submit pull requests.

## License
[MIT License](LICENSE)
