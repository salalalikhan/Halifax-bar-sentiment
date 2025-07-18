import React from 'react';
import { useParams } from 'react-router-dom';
import {
  Container,
  Typography,
  Paper,
  Box,
  Alert,
} from '@mui/material';

const BarDetail: React.FC = () => {
  const { barName } = useParams<{ barName: string }>();

  return (
    <Container maxWidth="lg">
      <Typography variant="h3" component="h1" gutterBottom>
        {decodeURIComponent(barName || '')}
      </Typography>
      
      <Paper sx={{ p: 3, mt: 3 }}>
        <Alert severity="info">
          🚧 Bar detail page is under construction. This will show detailed analytics, 
          recent mentions, sentiment trends, and more for the selected bar.
        </Alert>
      </Paper>
    </Container>
  );
};

export default BarDetail;