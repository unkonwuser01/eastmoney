import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Typography, 
  Button, 
  Grid, 
  IconButton, 
  TextField, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions,
  Autocomplete,
  CircularProgress,
  Chip,
  Box,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  TableHead,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Snackbar,
  Alert
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import SearchIcon from '@mui/icons-material/Search';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import EditIcon from '@mui/icons-material/Edit';
import BusinessIcon from '@mui/icons-material/Business';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import WbSunnyIcon from '@mui/icons-material/WbSunny';
import NightsStayIcon from '@mui/icons-material/NightsStay';

import {
  fetchStocks,
  saveStock,
  deleteStock,
  searchMarketStocks,
  fetchStockDetails,
  fetchStockHistory,
  analyzeStock
} from '../api';

import type { MarketStock, StockItem, StockDetails, NavPoint } from '../api';

export default function StocksPage() {
  const { t } = useTranslation();
  const [stocks, setStocks] = useState<StockItem[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Unified Dialog State (Add/Edit)
  const [openDialog, setOpenDialog] = useState(false);
  const [editingStock, setEditingStock] = useState<StockItem | null>(null);
  const [formCode, setFormCode] = useState('');
  const [formName, setFormName] = useState('');
  const [formMarket, setFormMarket] = useState('');

  // Search State
  const [searchResults, setSearchResults] = useState<MarketStock[]>([]);
  const [searching, setSearching] = useState(false);
  const [inputValue, setInputValue] = useState('');

  // Detail View State
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedStock, setSelectedStock] = useState<StockItem | null>(null);
  const [stockDetails, setStockDetails] = useState<StockDetails | null>(null);
  const [history, setHistory] = useState<NavPoint[]>([]);
  const [loadingDetails, setLoadingDetails] = useState(false);

  // Action Menu State
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuStock, setMenuStock] = useState<StockItem | null>(null);

  // Notification State
  const [notify, setNotify] = useState<{ open: boolean, message: string, severity: 'success' | 'info' | 'warning' | 'error' }>({
    open: false,
    message: '',
    severity: 'info'
  });

  const showNotify = (message: string, severity: 'success' | 'info' | 'warning' | 'error' = 'info') => { 
    setNotify({ open: true, message, severity });
  };

  const handleOpenMenu = (event: React.MouseEvent<HTMLElement>, stock: StockItem) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    setMenuStock(stock);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
    setMenuStock(null);
  };

  const handleOpenDialog = (stock?: StockItem) => {
    setAnchorEl(null);
    setSearchResults([]);
    setInputValue('');
    if (stock) {
        setEditingStock(stock);
        setFormCode(stock.code);
        setFormName(stock.name);
        setFormMarket(stock.market || '');
    } else {
        setEditingStock(null);
        setFormCode('');
        setFormName('');
        setFormMarket('');
    }
    setOpenDialog(true);
  };

  const handleSave = async () => {
    if (!formCode || !formName) {
        showNotify(t('stocks.messages.required_fields'), 'error');
        return;
    }

    const updatedStock: StockItem = {
        code: formCode,
        name: formName,
        market: formMarket,
        is_active: true,
        sector: editingStock?.sector || '' // Preserve existing sector if editing, else empty for auto-fetch
    };

    try {
        await saveStock(updatedStock);
        showNotify(t('stocks.messages.save_success'), 'success');
        setOpenDialog(false);
        loadStocks();
    } catch (error) {
        console.error(error);
        showNotify(t('stocks.messages.save_error'), 'error');
    }
  };

  const handleSearch = async (query: string) => {
    if (query.length < 2) return;
    setSearching(true);
    try {
      const results = await searchMarketStocks(query);
      setSearchResults(results);
    } catch (error) {
      console.error(error);
    } finally {
      setSearching(false);
    }
  };

  const handleMarketStockSelect = (_event: any, value: MarketStock | null) => {
    if (value) {
        setFormCode(value.code);
        setFormName(value.name);
    }
  };

  useEffect(() => {
    loadStocks();
  }, []);

  const loadStocks = async () => {
    setLoading(true);
    try {
      const data = await fetchStocks();
      setStocks(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (code: string) => {
    if (window.confirm(t('stocks.messages.delete_confirm'))) {
      try {
        await deleteStock(code);
        showNotify(t('stocks.messages.delete_success'), 'success');
        loadStocks();
      } catch (error) {
        showNotify(`${t('stocks.messages.delete_error')}: ${error}`, 'error');
      }
    }
  };

  const handleViewDetails = async (stock: StockItem) => {
    setSelectedStock(stock);
    setDetailOpen(true);
    setLoadingDetails(true);
    setStockDetails(null);
    setHistory([]);

    try {
      const [details, hist] = await Promise.all([
          fetchStockDetails(stock.code),
          fetchStockHistory(stock.code)
      ]);
      setStockDetails(details);
      setHistory(hist);
    } catch (error) {
      console.error("Failed to load stock details", error);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleAnalyzeStock = async (stock: StockItem, mode: 'pre' | 'post') => {
    handleCloseMenu();
    showNotify(t('stocks.messages.analysis_started', { name: stock.name, mode: mode === 'pre' ? t('stocks.analysis.pre_market') : t('stocks.analysis.post_market') }), 'info');
    try {
      await analyzeStock(stock.code, mode);
      showNotify(t('stocks.messages.analysis_success', { name: stock.name }), 'success');
    } catch (error) {
      console.error('Analysis failed:', error);
      showNotify(t('stocks.messages.analysis_error'), 'error');
    }
  };

  const renderMiniChart = (data: NavPoint[]) => {
    if (!data || data.length < 2) return null;
    const values = data.map(d => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min;
    const padding = 20;
    const width = 800;
    const height = 240;
    
    const points = data.map((d, i) => {
      const x = (i / (data.length - 1)) * (width - 2 * padding) + padding;
      const y = (height - padding) - ((d.value - min) / range) * (height - 2 * padding);
      return `${x},${y}`;
    }).join(' ');

    return (
      <Box sx={{ bgcolor: '#fcfcfc', p: 2, borderRadius: '12px', border: '1px solid #f1f5f9' }}>
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-48 overflow-visible">
          {[0, 0.25, 0.5, 0.75, 1].map((v) => {
              const y = (height - padding) - v * (height - 2 * padding);
              const val = (min + v * range).toFixed(2);
              return (
                  <g key={v}>
                      <line x1={padding} y1={y} x2={width-padding} y2={y} stroke="#e2e8f0" strokeDasharray="4 4" />
                      <text x={0} y={y + 4} fontSize="10" fill="#94a3b8" fontFamily="JetBrains Mono">{val}</text>
                  </g>
              )
          })}
          <polyline
            fill="none"
            stroke="#6366f1"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
          />
          <path
            d={`M${padding},${height-padding} L${points} L${width-padding},${height-padding} Z`}
            fill="rgba(99, 102, 241, 0.08)"
          />
        </svg>
      </Box>
    );
  };

  return (
    <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 4 }}>
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Typography variant="h4" className="font-bold text-slate-900" sx={{ fontFamily: 'JetBrains Mono' }}>
            {t('stocks.title')}
          </Typography>
          <Typography variant="subtitle1" className="text-slate-500 mt-1">
            {t('stocks.subtitle')}
          </Typography>
        </div>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
          sx={{
            backgroundColor: '#6366f1',
            borderRadius: '10px',
            px: 3,
            textTransform: 'none',
            fontWeight: 600,
            '&:hover': { backgroundColor: '#4f46e5' }
          }}
        >
          {t('stocks.add_stock')}
        </Button>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <CircularProgress size={32} sx={{ color: '#6366f1' }} />
        </div>
      ) : (
        <TableContainer component={Paper} elevation={0} sx={{ borderRadius: '16px', border: '1px solid #f1f5f9', overflow: 'hidden' }}>
          <Table sx={{ minWidth: 650 }}>
            <TableHead sx={{ bgcolor: '#f8fafc' }}>
              <TableRow>
                <TableCell sx={{ color: '#64748b', fontWeight: 800, fontSize: '0.75rem', py: 2 }}>{t('stocks.table.symbol')}</TableCell>
                <TableCell align="right" sx={{ color: '#64748b', fontWeight: 800, fontSize: '0.75rem', py: 2 }}>{t('stocks.table.latest_price')}</TableCell>
                <TableCell align="right" sx={{ color: '#64748b', fontWeight: 800, fontSize: '0.75rem', py: 2 }}>{t('common.change')}</TableCell>
                <TableCell align="right" sx={{ color: '#64748b', fontWeight: 800, fontSize: '0.75rem', py: 2 }}>{t('stocks.table.volume')}</TableCell>
                <TableCell sx={{ color: '#64748b', fontWeight: 800, fontSize: '0.75rem', py: 2 }}>{t('stocks.table.sector')}</TableCell>
                <TableCell align="right" sx={{ color: '#64748b', fontWeight: 800, fontSize: '0.75rem', py: 2 }}>{t('common.actions')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {stocks.map((stock) => (
                <TableRow 
                  key={stock.code} 
                  hover 
                  onClick={() => handleViewDetails(stock)}
                  sx={{ cursor: 'pointer', '&:last-child td, &:last-child th': { border: 0 } }}
                >
                  <TableCell sx={{ py: 2.5 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ p: 1, bgcolor: '#f1f5f9', borderRadius: '10px', color: '#6366f1' }}>    
                        <ShowChartIcon fontSize="small" />
                      </Box>
                      <Box>
                        <Typography sx={{ fontWeight: 800, color: '#1e293b', fontSize: '0.9rem' }}>{stock.name}</Typography>
                        <Typography sx={{ color: '#94a3b8', fontFamily: 'JetBrains Mono', fontSize: '0.75rem' }}>{stock.code}</Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Typography sx={{ fontWeight: 700, color: '#1e293b', fontFamily: 'JetBrains Mono' }}>
                        {stock.price ? stock.price.toFixed(2) : '---'}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography sx={{ 
                        fontWeight: 800, 
                        color: (stock.change_pct || 0) >= 0 ? '#ef4444' : '#22c55e', 
                        fontFamily: 'JetBrains Mono' 
                    }}>
                        {stock.change_pct ? `${stock.change_pct > 0 ? '+' : ''}${stock.change_pct.toFixed(2)}%` : '---'}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography sx={{ color: '#64748b', fontSize: '0.75rem', fontWeight: 700, fontFamily: 'JetBrains Mono' }}>
                        {stock.volume ? (stock.volume / 100).toLocaleString() : '---'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {stock.sector && (
                        <Chip 
                        label={stock.sector} 
                        size="small" 
                        variant="outlined" 
                        sx={{ 
                            fontSize: '0.65rem', 
                            fontWeight: 800, 
                            color: '#64748b', 
                            bgcolor: '#f8fafc',
                            border: '1px solid #e2e8f0',
                            borderRadius: '6px'
                        }} 
                        />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton 
                      size="small" 
                      onClick={(e) => handleOpenMenu(e, stock)}
                      sx={{ color: '#94a3b8', '&:hover': { color: '#6366f1', bgcolor: 'rgba(99, 102, 241, 0.05)' } }}
                    >
                      <MoreVertIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Notifications */}
      <Snackbar 
        open={notify.open} 
        autoHideDuration={4000} 
        onClose={() => setNotify(prev => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert severity={notify.severity} sx={{ width: '100%', borderRadius: '10px', fontWeight: 700, boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}>
          {notify.message}
        </Alert>
      </Snackbar>

      {/* Stock Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        PaperProps={{
            elevation: 2,
            sx: {
                minWidth: 200,
                bgcolor: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '12px',
                mt: 1,
                boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'
            }
        }}
      >
        <MenuItem onClick={() => { handleCloseMenu(); if (menuStock) handleViewDetails(menuStock); }} sx={{ py: 1.5 }}>
            <ListItemIcon><AnalyticsIcon fontSize="small" sx={{ color: '#6366f1' }} /></ListItemIcon>
            <ListItemText primary={t('stocks.menu.view_details')} primaryTypographyProps={{ fontSize: '0.85rem', fontWeight: 700 }} />
        </MenuItem>

        <Divider sx={{ my: 0.5, borderColor: '#f1f5f9' }} />

        <MenuItem onClick={() => { if (menuStock) handleAnalyzeStock(menuStock, 'pre'); }} sx={{ py: 1 }}>
            <ListItemIcon><WbSunnyIcon fontSize="small" sx={{ color: '#f59e0b' }} /></ListItemIcon>
            <ListItemText primary={t('stocks.menu.pre_market_analysis')} primaryTypographyProps={{ fontSize: '0.85rem', color: '#334155' }} />
        </MenuItem>
        <MenuItem onClick={() => { if (menuStock) handleAnalyzeStock(menuStock, 'post'); }} sx={{ py: 1 }}>
            <ListItemIcon><NightsStayIcon fontSize="small" sx={{ color: '#8b5cf6' }} /></ListItemIcon>
            <ListItemText primary={t('stocks.menu.post_market_analysis')} primaryTypographyProps={{ fontSize: '0.85rem', color: '#334155' }} />
        </MenuItem>

        <Divider sx={{ my: 0.5, borderColor: '#f1f5f9' }} />

        <MenuItem onClick={() => { handleCloseMenu(); if (menuStock) handleOpenDialog(menuStock); }} sx={{ py: 1 }}>
            <ListItemIcon><EditIcon fontSize="small" sx={{ color: '#64748b' }} /></ListItemIcon>
            <ListItemText primary={t('stocks.menu.edit_config')} primaryTypographyProps={{ fontSize: '0.85rem', color: '#334155' }} />
        </MenuItem>
        <MenuItem onClick={() => { handleCloseMenu(); if (menuStock) handleDelete(menuStock.code); }} sx={{ py: 1 }}>
            <ListItemIcon><DeleteIcon fontSize="small" color="error" /></ListItemIcon>
            <ListItemText primary={t('common.delete')} primaryTypographyProps={{ fontSize: '0.85rem', color: '#f43f5e', fontWeight: 700 }} />
        </MenuItem>
      </Menu>

      {/* Add/Edit Stock Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 800, borderBottom: '1px solid #f1f5f9' }}>
            {editingStock ? t('stocks.dialog.edit_title') : t('stocks.dialog.add_title')}
        </DialogTitle>
        <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 3 }}>
                
                {/* 1. Market Search */}
                {!editingStock && (
                    <Box>
                        <Typography variant="overline" sx={{ color: '#64748b', fontWeight: 800, mb: 1, display: 'block' }}>{t('stocks.dialog.market_search')}</Typography>
                        <Autocomplete
                            fullWidth
                            inputValue={inputValue}
                            onInputChange={(_, newInputValue) => setInputValue(newInputValue)}
                            onChange={handleMarketStockSelect}
                            options={searchResults}
                            getOptionLabel={(option) => `[${option.code}] ${option.name}`}
                            loading={searching}
                            renderInput={(params) => (
                            <TextField
                                {...params}
                                label={t('stocks.dialog.search_placeholder')}
                                variant="outlined"
                                size="small"
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                        e.preventDefault();
                                        handleSearch(inputValue);
                                    }
                                }}
                                InputProps={{
                                ...params.InputProps,
                                startAdornment: (
                                    <>
                                    <SearchIcon className="text-slate-400 mr-2" />
                                    {params.InputProps.startAdornment}
                                    </>
                                ),
                                endAdornment: (
                                    <>
                                    {searching ? <CircularProgress color="inherit" size={20} /> : null}
                                    {params.InputProps.endAdornment}
                                    </>
                                ),
                                }}
                            />
                            )}
                        />
                    </Box>
                )}

                {/* 2. Asset Identity */}
                <Box>
                    <Typography variant="overline" sx={{ color: '#64748b', fontWeight: 800, mb: 1, display: 'block' }}>{t('stocks.dialog.stock_info')}</Typography>
                    <Grid container spacing={2}>
                        <Grid size={4}>
                            <TextField
                                label={t('common.code')}
                                fullWidth
                                size="small"
                                value={formCode}
                                onChange={(e) => setFormCode(e.target.value)}
                                disabled={!!editingStock}
                                placeholder="000000"
                            />
                        </Grid>
                        <Grid size={8}>
                            <TextField
                                label={t('common.name')}
                                fullWidth
                                size="small"
                                value={formName}
                                onChange={(e) => setFormName(e.target.value)}
                                placeholder={t('stocks.dialog.name_placeholder')}
                            />
                        </Grid>
                    </Grid>
                </Box>

                {/* 3. Config */}
                <Box>
                    <Typography variant="overline" sx={{ color: '#64748b', fontWeight: 800, mb: 1, display: 'block' }}>{t('stocks.dialog.config')}</Typography>
                    <Grid container spacing={2}>
                        <Grid size={6}>
                            <Box sx={{ p: 1.5, bgcolor: '#f8fafc', borderRadius: '8px', border: '1px dashed #cbd5e1' }}>
                                <Typography variant="caption" sx={{ color: '#64748b', display: 'block', mb: 0.5, fontWeight: 700 }}>{t('stocks.dialog.sector')}</Typography>
                                <Typography variant="body2" sx={{ color: '#334155', fontWeight: 500 }}>
                                    {editingStock?.sector || (formCode ? "Auto-detected upon save" : "---")}
                                </Typography>
                            </Box>
                        </Grid>
                        <Grid size={6}>
                            <TextField
                                label={t('stocks.dialog.market')}
                                fullWidth
                                size="small"
                                value={formMarket}
                                onChange={(e) => setFormMarket(e.target.value)}
                                placeholder={t('stocks.dialog.market_placeholder')}
                            />
                        </Grid>
                    </Grid>
                </Box>
            </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3, borderTop: '1px solid #f1f5f9' }}>
          <Button onClick={() => setOpenDialog(false)} sx={{ color: '#64748b', fontWeight: 700 }}>{t('common.cancel')}</Button>
          <Button 
            onClick={handleSave} 
            variant="contained" 
            sx={{ bgcolor: '#6366f1', fontWeight: 800, borderRadius: '8px', px: 4, '&:hover': { bgcolor: '#4f46e5' } }}
          >
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Stock Details Dialog */}
      <Dialog 
        open={detailOpen} 
        onClose={() => setDetailOpen(false)} 
        maxWidth="sm" 
        fullWidth
        scroll="paper"
        PaperProps={{ 
          sx: { 
            borderRadius: '20px', 
            bgcolor: '#ffffff', 
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          } 
        }}
      >
        <DialogTitle sx={{ p: 0 }}>
          <Box sx={{ 
            bgcolor: '#fcfcfc', 
            p: 3.5, 
            borderBottom: '1px solid #f1f5f9',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start'
          }}>
             <Box>
                <Typography variant="h5" sx={{ fontWeight: 900, color: '#0f172a', letterSpacing: '-0.02em', mb: 1 }}>
                    {selectedStock?.name}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
                    <Box sx={{ px: 1, py: 0.25, bgcolor: '#6366f1', borderRadius: '4px' }}>
                        <Typography sx={{ color: '#fff', fontWeight: 800, fontFamily: 'JetBrains Mono', fontSize: '0.75rem' }}>
                            {selectedStock?.code}
                        </Typography>
                    </Box>
                </Box>
             </Box>
             <Box sx={{ textAlign: 'right' }}>
                 <Typography variant="h4" sx={{ 
                     fontWeight: 900, fontFamily: 'JetBrains Mono',
                     color: (stockDetails?.quote?.涨跌幅 > 0) ? '#ef4444' : (stockDetails?.quote?.涨跌幅 < 0) ? '#22c55e' : '#0f172a'
                 }}>
                    {stockDetails?.quote?.最新价 || '---'}
                 </Typography>
                 <Typography sx={{ 
                     fontWeight: 800, fontFamily: 'JetBrains Mono', fontSize: '0.9rem',
                     color: (stockDetails?.quote?.涨跌幅 > 0) ? '#ef4444' : (stockDetails?.quote?.涨跌幅 < 0) ? '#22c55e' : '#64748b'
                 }}>
                     {stockDetails?.quote?.涨跌幅 ? `${stockDetails.quote.涨跌幅}%` : '---'}
                 </Typography>
             </Box>
          </Box>
        </DialogTitle>

        <DialogContent sx={{ p: 0, bgcolor: '#ffffff' }}>
          {loadingDetails ? (
            <Box sx={{ py: 12, textAlign: 'center' }}>
              <CircularProgress size={32} thickness={5} sx={{ color: '#6366f1', mb: 2 }} />
            </Box>
          ) : stockDetails ? (
            <Box sx={{ p: 3.5, display: 'flex', flexDirection: 'column', gap: 4 }}>
                
                {/* 0. Chart Section */}
                <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="overline" sx={{ color: '#0f172a', fontWeight: 900, fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 1 }}>
                            <TrendingUpIcon sx={{ fontSize: 18, color: '#6366f1' }} /> {t('funds.details.performance_analytics')}
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 700 }}>{t('funds.details.last_100_days')}</Typography>
                    </Box>
                    {renderMiniChart(history)}
                </Box>

                {/* 1. Market Data */}
                <Box>
                    <Typography variant="overline" sx={{ color: '#0f172a', fontWeight: 900, fontSize: '0.75rem', mb: 2, display: 'block' }}>
                        {t('stocks.details.market_data')}
                    </Typography>
                    <Grid container spacing={2}>
                        <Grid size={4}>
                            <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 800 }}>{t('stocks.details.open')}</Typography>
                            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{stockDetails.quote?.今开 || '---'}</Typography>
                        </Grid>
                        <Grid size={4}>
                            <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 800 }}>{t('stocks.details.high')}</Typography>
                            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{stockDetails.quote?.最高 || '---'}</Typography>
                        </Grid>
                        <Grid size={4}>
                            <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 800 }}>{t('stocks.details.low')}</Typography>
                            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{stockDetails.quote?.最低 || '---'}</Typography>
                        </Grid>
                         <Grid size={4}>
                            <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 800 }}>{t('stocks.details.volume')}</Typography>
                            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{stockDetails.quote?.成交量 || '---'}</Typography>
                        </Grid>
                        <Grid size={4}>
                            <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 800 }}>{t('stocks.details.amount')}</Typography>
                            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{stockDetails.quote?.成交额 || '---'}</Typography>
                        </Grid>
                    </Grid>
                </Box>

                {/* 2. Company Info */}
                <Box>
                    <Typography variant="overline" sx={{ color: '#0f172a', fontWeight: 900, fontSize: '0.75rem', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                        <BusinessIcon sx={{ fontSize: 18, color: '#6366f1' }} /> {t('stocks.details.company_profile')}
                    </Typography>
                    <Grid container spacing={2}>
                        <Grid size={6}>
                            <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 800 }}>{t('stocks.details.industry')}</Typography>
                            <Typography variant="body2" sx={{ fontWeight: 700 }}>{stockDetails.info?.industry || '---'}</Typography>
                        </Grid>
                        <Grid size={6}>
                            <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 800 }}>{t('stocks.details.market_cap')}</Typography>
                            <Typography variant="body2" sx={{ fontWeight: 700 }}>{stockDetails.info?.market_cap || '---'}</Typography>
                        </Grid>
                        <Grid size={3}>
                             <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 800 }}>{t('stocks.details.pe')}</Typography>
                             <Typography variant="body2" sx={{ fontWeight: 700 }}>{stockDetails.info?.pe || '---'}</Typography>
                        </Grid>
                        <Grid size={3}>
                             <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 800 }}>{t('stocks.details.pb')}</Typography>
                             <Typography variant="body2" sx={{ fontWeight: 700 }}>{stockDetails.info?.pb || '---'}</Typography>
                        </Grid>
                    </Grid>
                </Box>

            </Box>
          ) : (
             <Box sx={{ py: 10, textAlign: 'center' }}>
                 <Typography sx={{ color: '#94a3b8' }}>{t('stocks.details.no_details')}</Typography>
             </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 3, bgcolor: '#fcfcfc', borderTop: '1px solid #f1f5f9' }}>
          <Button 
            fullWidth
            onClick={() => setDetailOpen(false)} 
            variant="contained" 
            sx={{ 
                bgcolor: '#0f172a', 
                color: '#ffffff',
                py: 1.5,
                borderRadius: '12px',
                fontWeight: 800,
                boxShadow: 'none',
                '&:hover': { bgcolor: '#1e293b' }
            }}
          >
            {t('stocks.details.close')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}