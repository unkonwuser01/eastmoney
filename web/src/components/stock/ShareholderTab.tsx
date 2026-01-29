import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Typography,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Tabs,
  Tab
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import GroupsIcon from '@mui/icons-material/Groups';
import { fetchStockShareholders } from '../../api';
import type { ShareholderData } from '../../api';

interface ShareholderTabProps {
  code: string;
}

export default function ShareholderTab({ code }: ShareholderTabProps) {
  const { t } = useTranslation();
  const [data, setData] = useState<ShareholderData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState(0);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchStockShareholders(code);
        setData(result);
      } catch (err) {
        setError(t('stocks.professional.load_error'));
        console.error('Failed to load shareholder data:', err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [code, t]);

  if (loading) {
    return (
      <Box sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress size={32} sx={{ color: '#6366f1' }} />
        <Typography sx={{ mt: 2, color: '#64748b' }}>{t('common.loading')}</Typography>
      </Box>
    );
  }

  if (error || !data) {
    return (
      <Box sx={{ py: 8, textAlign: 'center' }}>
        <Typography color="error">{error || t('stocks.professional.no_data')}</Typography>
      </Box>
    );
  }

  const formatNumber = (val?: number) => {
    if (val == null) return '---';
    if (val >= 100000000) return `${(val / 100000000).toFixed(2)}${t('stocks.shareholder.unit_yi')}`;
    if (val >= 10000) return `${(val / 10000).toFixed(2)}${t('stocks.shareholder.unit_wan')}`;
    return val.toLocaleString();
  };

  const formatPercent = (val?: number) => val != null ? `${val.toFixed(2)}%` : '---';

  // Prepare holder number trend for chart
  const holderTrend = (data.holder_number_trend || [])
    .slice()
    .reverse()
    .map(h => ({
      period: h.end_date?.substring(0, 6) || '',
      value: h.holder_num || 0
    }));

  const renderTrendChart = (dataPoints: { period: string; value: number }[]) => {
    if (dataPoints.length < 2) return null;
    const values = dataPoints.map(d => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    const width = 300;
    const height = 100;
    const padding = 15;

    const points = dataPoints.map((d, i) => {
      const x = (i / (dataPoints.length - 1)) * (width - 2 * padding) + padding;
      const y = (height - padding) - ((d.value - min) / range) * (height - 2 * padding);
      return `${x},${y}`;
    }).join(' ');

    return (
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 100 }}>
        <polyline
          fill="none"
          stroke="#8b5cf6"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
        />
        <path
          d={`M${padding},${height - padding} L${points} L${width - padding},${height - padding} Z`}
          fill="rgba(139, 92, 246, 0.1)"
        />
      </svg>
    );
  };

  const currentPeriodHolders = (data.top10_holders || [])[selectedPeriod]?.holders || [];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Concentration Change Card */}
      {data.concentration_change && (
        <Paper elevation={0} sx={{ p: 3, bgcolor: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{
                width: 48, height: 48, borderRadius: '12px',
                bgcolor: data.concentration_change.signal === 'positive' ? '#22c55e20' :
                         data.concentration_change.signal === 'negative' ? '#ef444420' : '#64748b20',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                <GroupsIcon sx={{
                  color: data.concentration_change.signal === 'positive' ? '#22c55e' :
                         data.concentration_change.signal === 'negative' ? '#ef4444' : '#64748b',
                  fontSize: 24
                }} />
              </Box>
              <Box>
                <Typography variant="overline" sx={{ color: '#64748b', fontWeight: 800 }}>
                  {t('stocks.shareholder.concentration')}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {data.concentration_change.trend === 'decreasing' ? (
                    <TrendingDownIcon sx={{ color: '#22c55e', fontSize: 20 }} />
                  ) : (
                    <TrendingUpIcon sx={{ color: '#ef4444', fontSize: 20 }} />
                  )}
                  <Typography variant="h5" sx={{
                    fontWeight: 900,
                    color: data.concentration_change.trend === 'decreasing' ? '#22c55e' : '#ef4444'
                  }}>
                    {data.concentration_change.value > 0 ? '+' : ''}{data.concentration_change.value.toFixed(2)}%
                  </Typography>
                </Box>
              </Box>
            </Box>
            <Chip
              label={data.concentration_change.trend === 'decreasing' ?
                t('stocks.shareholder.concentrating') : t('stocks.shareholder.dispersing')}
              sx={{
                bgcolor: data.concentration_change.trend === 'decreasing' ? '#22c55e20' : '#ef444420',
                color: data.concentration_change.trend === 'decreasing' ? '#22c55e' : '#ef4444',
                fontWeight: 800
              }}
            />
          </Box>
          <Typography variant="caption" sx={{ color: '#94a3b8', mt: 1, display: 'block' }}>
            {data.concentration_change.trend === 'decreasing' ?
              t('stocks.shareholder.concentration_tip_positive') :
              t('stocks.shareholder.concentration_tip_negative')}
          </Typography>
        </Paper>
      )}

      {/* Holder Number Trend */}
      {holderTrend.length > 1 && (
        <Box>
          <Typography variant="overline" sx={{ color: '#0f172a', fontWeight: 900, mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <GroupsIcon sx={{ fontSize: 18, color: '#8b5cf6' }} />
            {t('stocks.shareholder.holder_trend')}
          </Typography>
          <Paper elevation={0} sx={{ p: 2, bgcolor: '#fcfcfc', borderRadius: '10px', border: '1px solid #f1f5f9' }}>
            {renderTrendChart(holderTrend)}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
              {holderTrend.filter((_, i) => i % Math.ceil(holderTrend.length / 6) === 0).map((d, i) => (
                <Typography key={i} variant="caption" sx={{ color: '#94a3b8', fontSize: '0.65rem' }}>
                  {d.period}
                </Typography>
              ))}
            </Box>
          </Paper>
        </Box>
      )}

      {/* Top 10 Holders Table */}
      {(data.top10_holders || []).length > 0 && (
        <Box>
          <Typography variant="overline" sx={{ color: '#0f172a', fontWeight: 900, mb: 1, display: 'block' }}>
            {t('stocks.shareholder.top10')}
          </Typography>

          {/* Period Tabs */}
          <Tabs
            value={selectedPeriod}
            onChange={(_, val) => setSelectedPeriod(val)}
            sx={{ mb: 2, minHeight: 32 }}
            TabIndicatorProps={{ sx: { bgcolor: '#6366f1' } }}
          >
            {(data.top10_holders || []).slice(0, 4).map((period, i) => (
              <Tab
                key={i}
                label={period.period?.substring(0, 4) + '-Q' + Math.ceil(parseInt(period.period?.substring(4, 6) || '3') / 3)}
                sx={{
                  minHeight: 32,
                  py: 0.5,
                  px: 2,
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  textTransform: 'none',
                  '&.Mui-selected': { color: '#6366f1' }
                }}
              />
            ))}
          </Tabs>

          <TableContainer component={Paper} elevation={0} sx={{ borderRadius: '10px', border: '1px solid #f1f5f9' }}>
            <Table size="small">
              <TableHead sx={{ bgcolor: '#f8fafc' }}>
                <TableRow>
                  <TableCell sx={{ fontWeight: 800, fontSize: '0.7rem', color: '#64748b' }}>#</TableCell>
                  <TableCell sx={{ fontWeight: 800, fontSize: '0.7rem', color: '#64748b' }}>{t('stocks.shareholder.holder_name')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 800, fontSize: '0.7rem', color: '#64748b' }}>{t('stocks.shareholder.hold_amount')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 800, fontSize: '0.7rem', color: '#64748b' }}>{t('stocks.shareholder.hold_ratio')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {currentPeriodHolders.slice(0, 10).map((holder, i) => (
                  <TableRow key={i} hover>
                    <TableCell sx={{ py: 1.5 }}>
                      <Chip
                        label={i + 1}
                        size="small"
                        sx={{
                          minWidth: 24,
                          height: 24,
                          fontSize: '0.7rem',
                          fontWeight: 800,
                          bgcolor: i < 3 ? '#6366f120' : '#f1f5f9',
                          color: i < 3 ? '#6366f1' : '#64748b'
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ py: 1.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.8rem', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {holder.holder_name || '---'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right" sx={{ py: 1.5 }}>
                      <Typography variant="body2" sx={{ fontFamily: 'JetBrains Mono', fontWeight: 600, fontSize: '0.8rem' }}>
                        {formatNumber(holder.hold_amount)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right" sx={{ py: 1.5 }}>
                      <Typography variant="body2" sx={{ fontFamily: 'JetBrains Mono', fontWeight: 700, fontSize: '0.8rem', color: '#6366f1' }}>
                        {formatPercent(holder.hold_ratio)}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}
    </Box>
  );
}
