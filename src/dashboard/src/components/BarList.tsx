import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Box,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { ApiService, handleApiError } from '../services/api';
import { BarSummary } from '../types/api';

const BarList: React.FC = () => {
  const [bars, setBars] = useState<BarSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBars = async () => {
      try {
        setLoading(true);
        setError(null);
        const barsData = await ApiService.getBars();
        setBars(barsData);
      } catch (err) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };

    fetchBars();
  }, []);

  const getSentimentColor = (score: number): 'success' | 'warning' | 'error' => {
    if (score > 0.1) return 'success';
    if (score < -0.1) return 'error';
    return 'warning';
  };

  const getSentimentLabel = (score: number): string => {
    if (score > 0.1) return 'Positive';
    if (score < -0.1) return 'Negative';
    return 'Neutral';
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
        Halifax Bars ({bars.length})
      </Typography>
      
      <Grid container spacing={3}>
        {bars.map((bar) => (
          <Grid item xs={12} sm={6} md={4} key={bar.name}>
            <Card>
              <CardContent>
                <Typography variant="h6" component="h2" gutterBottom>
                  {bar.name}
                </Typography>
                
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <Typography variant="body2" color="textSecondary">
                    {bar.total_mentions.toLocaleString()} mentions
                  </Typography>
                  <Chip
                    label={getSentimentLabel(bar.avg_sentiment)}
                    color={getSentimentColor(bar.avg_sentiment)}
                    size="small"
                  />
                </Box>
                
                <Typography variant="body2" color="textSecondary">
                  Avg Sentiment: {bar.avg_sentiment.toFixed(3)}
                </Typography>
                
                <Typography variant="body2" color="textSecondary">
                  Confidence: {(bar.avg_confidence * 100).toFixed(1)}%
                </Typography>
                
                {bar.specialties && bar.specialties.length > 0 && (
                  <Box mt={1}>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Specialties:
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={0.5}>
                      {bar.specialties.slice(0, 3).map((specialty) => (
                        <Chip
                          key={specialty}
                          label={specialty}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Box>
                )}
              </CardContent>
              
              <CardActions>
                <Button
                  component={RouterLink}
                  to={`/bars/${encodeURIComponent(bar.name)}`}
                  size="small"
                  color="primary"
                >
                  View Details
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default BarList;