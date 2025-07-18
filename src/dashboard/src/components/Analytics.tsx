import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Grid,
  Box,
  MenuItem,
  Button,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

import { ApiService, handleApiError } from '../services/api';
import { TrendRequest, TrendResponse, ComparisonRequest, ComparisonResponse } from '../types/api';

const SENTIMENT_COLORS = {
  positive: '#4caf50',
  negative: '#f44336',
  neutral: '#ff9800',
};

const Analytics: React.FC = () => {
  const [trendData, setTrendData] = useState<TrendResponse | null>(null);
  const [comparisonData, setComparisonData] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Trend filters
  const [trendPeriod, setTrendPeriod] = useState<number>(30);
  const [trendGranularity, setTrendGranularity] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [selectedBars] = useState<string[]>([]);
  
  // Comparison filters
  const [comparisonBars] = useState<string[]>(['Your Father\'s Moustache', 'The Bitter End', 'Good Robot']);
  const [comparisonPeriod] = useState<number>(30);
  const [comparisonMetrics] = useState<string[]>(['avg_sentiment', 'total_mentions']);

  const fetchTrendData = async () => {
    if (loading) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const trendRequest: TrendRequest = {
        days: trendPeriod,
        granularity: trendGranularity,
        bars: selectedBars.length > 0 ? selectedBars : undefined,
      };
      
      const response = await ApiService.getSentimentTrends(trendRequest);
      setTrendData(response);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const fetchComparisonData = async () => {
    if (loading || comparisonBars.length === 0) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const comparisonRequest: ComparisonRequest = {
        bars: comparisonBars,
        metrics: comparisonMetrics,
        days: comparisonPeriod,
      };
      
      const response = await ApiService.compareBars(comparisonRequest);
      setComparisonData(response);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrendData();
    fetchComparisonData();
  }, []);

  const handleTrendPeriodChange = (event: SelectChangeEvent<number>) => {
    setTrendPeriod(Number(event.target.value));
  };

  const handleGranularityChange = (event: SelectChangeEvent<string>) => {
    setTrendGranularity(event.target.value as 'daily' | 'weekly' | 'monthly');
  };

  const formatTrendData = () => {
    if (!trendData?.trends) return [];
    
    const groupedData: { [key: string]: any } = {};
    
    trendData.trends.forEach((trend) => {
      const dateKey = new Date(trend.date).toLocaleDateString();
      if (!groupedData[dateKey]) {
        groupedData[dateKey] = { date: dateKey };
      }
      
      groupedData[dateKey][trend.bar_name] = trend.avg_sentiment;
      groupedData[dateKey][`${trend.bar_name}_mentions`] = trend.mention_count;
    });
    
    return Object.values(groupedData).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  };

  const formatComparisonData = () => {
    if (!comparisonData?.comparison_data) return [];
    
    return Object.entries(comparisonData.comparison_data).map(([barName, data]: [string, any]) => ({
      name: barName,
      sentiment: data.avg_sentiment || 0,
      mentions: data.total_mentions || 0,
      confidence: data.avg_confidence || 0,
    }));
  };

  const getSentimentDistribution = () => {
    if (!trendData?.trends) return [];
    
    const totals = { positive: 0, negative: 0, neutral: 0 };
    
    trendData.trends.forEach((trend) => {
      totals.positive += trend.positive_count;
      totals.negative += trend.negative_count;
      totals.neutral += trend.neutral_count;
    });
    
    return [
      { name: 'Positive', value: totals.positive, color: SENTIMENT_COLORS.positive },
      { name: 'Negative', value: totals.negative, color: SENTIMENT_COLORS.negative },
      { name: 'Neutral', value: totals.neutral, color: SENTIMENT_COLORS.neutral },
    ];
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h3" component="h1" gutterBottom>
        Advanced Analytics
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Trend Analysis Controls */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Sentiment Trends
            </Typography>
            
            <Box display="flex" gap={2} alignItems="center" mb={2}>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Period</InputLabel>
                <Select value={trendPeriod} onChange={handleTrendPeriodChange}>
                  <MenuItem value={7}>7 days</MenuItem>
                  <MenuItem value={30}>30 days</MenuItem>
                  <MenuItem value={90}>90 days</MenuItem>
                  <MenuItem value={365}>1 year</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Granularity</InputLabel>
                <Select value={trendGranularity} onChange={handleGranularityChange}>
                  <MenuItem value="daily">Daily</MenuItem>
                  <MenuItem value="weekly">Weekly</MenuItem>
                  <MenuItem value="monthly">Monthly</MenuItem>
                </Select>
              </FormControl>
              
              <Button 
                variant="contained" 
                onClick={fetchTrendData}
                disabled={loading}
              >
                {loading ? <CircularProgress size={20} /> : 'Update Trends'}
              </Button>
            </Box>
            
            {trendData && (
              <Box sx={{ height: 400 }}>
                <ResponsiveContainer>
                  <LineChart data={formatTrendData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={[-1, 1]} />
                    <Tooltip />
                    {comparisonBars.map((bar, index) => (
                      <Line
                        key={bar}
                        type="monotone"
                        dataKey={bar}
                        stroke={`hsl(${(index * 360) / comparisonBars.length}, 70%, 50%)`}
                        strokeWidth={2}
                        dot={false}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Sentiment Distribution */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Sentiment Distribution
            </Typography>
            
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={getSentimentDistribution()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.name}: ${entry.value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {getSentimentDistribution().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>

        {/* Bar Comparison */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Bar Comparison
            </Typography>
            
            <Box display="flex" gap={2} mb={2}>
              <Button 
                variant="outlined" 
                onClick={fetchComparisonData}
                disabled={loading}
                size="small"
              >
                {loading ? <CircularProgress size={16} /> : 'Update'}
              </Button>
            </Box>
            
            <Box sx={{ height: 250 }}>
              <ResponsiveContainer>
                <BarChart data={formatComparisonData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="sentiment" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>

        {/* Summary Statistics */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Analytics Summary
            </Typography>
            
            <Grid container spacing={2}>
              {trendData?.summary_stats && (
                <>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="primary">
                        {trendData.summary_stats.total_mentions?.toLocaleString() || 'N/A'}
                      </Typography>
                      <Typography color="textSecondary">
                        Total Mentions
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="secondary">
                        {trendData.summary_stats.average_sentiment?.toFixed(3) || 'N/A'}
                      </Typography>
                      <Typography color="textSecondary">
                        Average Sentiment
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="success.main">
                        {trendData.summary_stats.bars_analyzed || 'N/A'}
                      </Typography>
                      <Typography color="textSecondary">
                        Bars Analyzed
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="info.main">
                        {trendData.summary_stats.period_days || 'N/A'}
                      </Typography>
                      <Typography color="textSecondary">
                        Days Analyzed
                      </Typography>
                    </Box>
                  </Grid>
                </>
              )}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Analytics;