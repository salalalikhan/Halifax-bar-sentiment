import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Box,
  Chip,
  LinearProgress,
} from '@mui/material';

import { ApiService, handleApiError } from '../services/api';
import { QualityMetrics } from '../types/api';

const DataQuality: React.FC = () => {
  const [metrics, setMetrics] = useState<QualityMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        setError(null);
        const metricsData = await ApiService.getQualityMetrics(10);
        setMetrics(metricsData);
      } catch (err) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  const getQualityColor = (score: number): 'success' | 'warning' | 'error' => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
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
        Data Quality Metrics
      </Typography>
      
      {metrics.length === 0 ? (
        <Alert severity="info" sx={{ mt: 3 }}>
          No quality metrics available yet. Run the data processing pipeline to generate metrics.
        </Alert>
      ) : (
        <TableContainer component={Paper} sx={{ mt: 3 }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Processing Date</TableCell>
                <TableCell align="right">Posts Processed</TableCell>
                <TableCell align="right">Valid Posts</TableCell>
                <TableCell align="right">Spam Filtered</TableCell>
                <TableCell align="right">Mentions Found</TableCell>
                <TableCell align="right">Avg Confidence</TableCell>
                <TableCell align="center">Quality Score</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {metrics.map((metric, index) => (
                <TableRow key={index}>
                  <TableCell>
                    {new Date(metric.processing_date).toLocaleString()}
                  </TableCell>
                  <TableCell align="right">
                    {metric.total_posts_processed.toLocaleString()}
                  </TableCell>
                  <TableCell align="right">
                    {metric.valid_posts.toLocaleString()}
                    <br />
                    <Typography variant="caption" color="textSecondary">
                      ({((metric.valid_posts / metric.total_posts_processed) * 100).toFixed(1)}%)
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    {metric.spam_filtered.toLocaleString()}
                  </TableCell>
                  <TableCell align="right">
                    {metric.mentions_found.toLocaleString()}
                  </TableCell>
                  <TableCell align="right">
                    {formatPercentage(metric.average_confidence)}
                  </TableCell>
                  <TableCell align="center">
                    <Box display="flex" flexDirection="column" alignItems="center" gap={1}>
                      <Chip
                        label={formatPercentage(metric.data_quality_score)}
                        color={getQualityColor(metric.data_quality_score)}
                        size="small"
                      />
                      <LinearProgress
                        variant="determinate"
                        value={metric.data_quality_score * 100}
                        color={getQualityColor(metric.data_quality_score)}
                        sx={{ width: 60, height: 4 }}
                      />
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Container>
  );
};

export default DataQuality;