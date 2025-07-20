import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Store,
  Assessment,
  Timeline,
} from '@mui/icons-material';

import { ApiService, handleApiError } from '../services/api';
import { AnalyticsSummary, BarSummary, HealthResponse } from '../types/api';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
  trend?: 'up' | 'down' | 'flat';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, subtitle, icon, color = 'primary', trend }) => {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp color="success" />;
      case 'down':
        return <TrendingDown color="error" />;
      case 'flat':
        return <TrendingFlat color="warning" />;
      default:
        return null;
    }
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="h2">
              {value}
            </Typography>
            {subtitle && (
              <Typography color="textSecondary" variant="body2">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box display="flex" flexDirection="column" alignItems="center">
            <Box color={`${color}.main`} mb={1}>
              {icon}
            </Box>
            {getTrendIcon()}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

const Dashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [topBars, setTopBars] = useState<BarSummary[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch data in parallel
        const [analyticsData, barsData, healthData] = await Promise.all([
          ApiService.getAnalyticsSummary().catch(() => null),
          ApiService.getBars(10).catch(() => []),
          ApiService.getHealth().catch(() => null),
        ]);

        setAnalytics(analyticsData);
        setTopBars(barsData);
        setHealth(healthData);
      } catch (err) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getSentimentLabel = (score: number): { label: string; color: 'success' | 'warning' | 'error' } => {
    if (score > 0.1) return { label: 'Positive', color: 'success' };
    if (score < -0.1) return { label: 'Negative', color: 'error' };
    return { label: 'Neutral', color: 'warning' };
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg">
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Typography variant="h3" component="h1" gutterBottom>
        Dashboard Overview
      </Typography>

      {health && (
        <Alert 
          severity={health.database_connected ? 'success' : 'error'} 
          sx={{ mb: 3 }}
        >
          System Status: {health.status} | Last Update: {health.last_data_update ? new Date(health.last_data_update).toLocaleString() : 'Never'}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Key Statistics */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Mentions"
            value={analytics?.total_mentions.toLocaleString() || 0}
            icon={<Assessment fontSize="large" />}
            color="primary"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Unique Bars"
            value={analytics?.unique_bars || 0}
            icon={<Store fontSize="large" />}
            color="secondary"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Sentiment"
            value={analytics?.avg_sentiment_score.toFixed(3) || '0.000'}
            subtitle={analytics ? getSentimentLabel(analytics.avg_sentiment_score).label : ''}
            icon={<Timeline fontSize="large" />}
            color="info"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Data Quality"
            value={analytics?.data_quality_score ? formatPercentage(analytics.data_quality_score) : 'N/A'}
            icon={<Assessment fontSize="large" />}
            color="success"
          />
        </Grid>

        {/* Sentiment Distribution */}
        {analytics?.sentiment_distribution && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Sentiment Distribution
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                {Object.entries(analytics.sentiment_distribution).map(([sentiment, count]) => {
                  const total = Object.values(analytics.sentiment_distribution).reduce((a, b) => a + b, 0);
                  const percentage = total > 0 ? (count / total) * 100 : 0;
                  const sentimentInfo = getSentimentLabel(sentiment === 'positive' ? 1 : sentiment === 'negative' ? -1 : 0);
                  
                  return (
                    <Box key={sentiment} display="flex" alignItems="center" justifyContent="space-between">
                      <Box display="flex" alignItems="center" gap={1}>
                        <Chip 
                          label={sentiment.charAt(0).toUpperCase() + sentiment.slice(1)} 
                          color={sentimentInfo.color}
                          size="small"
                        />
                        <Typography variant="body2">
                          {count.toLocaleString()} mentions
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="textSecondary">
                        {percentage.toFixed(1)}%
                      </Typography>
                    </Box>
                  );
                })}
              </Box>
            </Paper>
          </Grid>
        )}

        {/* Top Mentioned Bars */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Top Mentioned Bars
            </Typography>
            <Box display="flex" flexDirection="column" gap={1}>
              {topBars.slice(0, 8).map((bar, index) => {
                const sentimentInfo = getSentimentLabel(bar.avg_sentiment);
                
                return (
                  <Box key={bar.name} display="flex" alignItems="center" justifyContent="space-between">
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="body2" color="textSecondary" sx={{ minWidth: 20 }}>
                        {index + 1}.
                      </Typography>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                        {bar.name}
                      </Typography>
                    </Box>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="body2" color="textSecondary">
                        {bar.total_mentions} mentions
                      </Typography>
                      <Chip 
                        label={sentimentInfo.label}
                        color={sentimentInfo.color}
                        size="small"
                      />
                    </Box>
                  </Box>
                );
              })}
            </Box>
          </Paper>
        </Grid>

        {/* Trending Foods */}
        {analytics?.trending_foods && analytics.trending_foods.length > 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Trending Food & Drinks
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={1}>
                {analytics.trending_foods.slice(0, 15).map((item, index) => (
                  <Chip
                    key={item.food}
                    label={`${item.food} (${item.count})`}
                    variant="outlined"
                    color={index < 5 ? 'primary' : 'default'}
                  />
                ))}
              </Box>
            </Paper>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default Dashboard;