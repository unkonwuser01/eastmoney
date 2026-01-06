import { useState, useEffect, useMemo } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  TextField,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  IconButton,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Snackbar,
  Alert,
  Autocomplete,
  CircularProgress
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ScheduleIcon from '@mui/icons-material/Schedule';
import { fetchFunds, saveFund, deleteFund, generateReport, searchMarketFunds } from '../api';
import type { FundItem, MarketFund } from '../api';

interface HeadCell {
  id: keyof FundItem | 'schedule';
  label: string;
  minWidth?: number;
  align?: 'left' | 'right' | 'center';
}

const headCells: HeadCell[] = [
  { id: 'code', label: 'CODE', minWidth: 80 },
  { id: 'name', label: 'FUND NAME', minWidth: 180 },
  { id: 'style', label: 'STRATEGY', minWidth: 100 },
  { id: 'focus', label: 'SECTORS', minWidth: 150 },
  { id: 'schedule', label: 'SCHEDULE (24H)', minWidth: 120 },
];

export default function FundsPage() {
  const [funds, setFunds] = useState<FundItem[]>([]);
  // const [loading, setLoading] = useState(false); // Removed unused
  
  // Table State
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Dialog State
  const [openDialog, setOpenDialog] = useState(false);
  const [editingFund, setEditingFund] = useState<FundItem | null>(null);
  const [formCode, setFormCode] = useState('');
  const [formName, setFormName] = useState('');
  const [formStyle, setFormStyle] = useState('');
  const [formFocus, setFormFocus] = useState('');
  const [formPreTime, setFormPreTime] = useState('');
  const [formPostTime, setFormPostTime] = useState('');

  // Search State
  const [marketOptions, setMarketOptions] = useState<MarketFund[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Menu State
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuFund, setMenuFund] = useState<FundItem | null>(null);

  // Toast
  const [toast, setToast] = useState<{open: boolean, message: string, severity: 'success'|'info'|'error'}>({
    open: false, message: '', severity: 'info'
  });

  useEffect(() => {
    loadFunds();
  }, []);

  const loadFunds = async () => {
    // setLoading(true);
    try {
      const data = await fetchFunds();
      setFunds(data);
    } catch (error) {
      console.error("Failed to load funds", error);
      setToast({ open: true, message: 'Failed to load funds', severity: 'error' });
    } finally {
      // setLoading(false);
    }
  };

  // Filter & Pagination Logic
  const filteredFunds = useMemo(() => {
    return funds.filter(f => 
        f.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
        f.code.includes(searchQuery) ||
        f.style?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [funds, searchQuery]);

  const paginatedFunds = useMemo(() => {
    return filteredFunds.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  }, [filteredFunds, page, rowsPerPage]);

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(+event.target.value);
    setPage(0);
  };

  // CRUD Handlers
  const handleOpenDialog = (fund?: FundItem) => {
    setAnchorEl(null); // Close menu if open
    setMarketOptions([]);
    if (fund) {
        setEditingFund(fund);
        setFormCode(fund.code);
        setFormName(fund.name);
        setFormStyle(fund.style || '');
        setFormFocus(fund.focus?.join(', ') || '');
        setFormPreTime(fund.pre_market_time || '');
        setFormPostTime(fund.post_market_time || '');
    } else {
        setEditingFund(null);
        setFormCode('');
        setFormName('');
        setFormStyle('');
        setFormFocus('');
        // Set Defaults
        setFormPreTime('08:30');
        setFormPostTime('15:30');
    }
    setOpenDialog(true);
  };

  const handleSave = async () => {
    if (!formCode || !formName) {
        setToast({ open: true, message: 'Code and Name are required', severity: 'error' });
        return;
    }

    const focusArray = formFocus.split(/[,，]/).map(s => s.trim()).filter(Boolean);
    
    const newFund: FundItem = {
        code: formCode,
        name: formName,
        style: formStyle,
        focus: focusArray,
        pre_market_time: formPreTime || undefined,
        post_market_time: formPostTime || undefined
    };

    try {
        await saveFund(newFund);
        setToast({ open: true, message: 'Fund saved successfully', severity: 'success' });
        setOpenDialog(false);
        loadFunds(); // Reload from server to get sync state
    } catch (error) {
        setToast({ open: true, message: 'Failed to save fund', severity: 'error' });
    }
  };

  const handleDelete = async (code: string) => {
    setAnchorEl(null);
    if (!confirm("Delete this fund? This will also remove its scheduled tasks.")) return;
    try {
        await deleteFund(code);
        setToast({ open: true, message: 'Fund deleted', severity: 'success' });
        loadFunds();
    } catch (error) {
        setToast({ open: true, message: 'Failed to delete fund', severity: 'error' });
    }
  };

  // Search Logic
  const handleFundSearch = async (_event: any, value: string) => {
    if (!value || value.length < 2) { // Only search if length >= 2 to save API calls
        setMarketOptions([]);
        return;
    }
    setSearchLoading(true);
    try {
        const results = await searchMarketFunds(value);
        setMarketOptions(results);
    } catch (e) {
        console.error(e);
    } finally {
        setSearchLoading(false);
    }
  };

  const handleFundSelect = (_event: any, value: MarketFund | null) => {
    if (value) {
        setFormCode(value.code);
        setFormName(value.name);
        setFormStyle(value.type || '');
    }
  };

  // Menu Handlers
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, fund: FundItem) => {
    setAnchorEl(event.currentTarget);
    setMenuFund(fund);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuFund(null);
  };

  const handleRunAnalysis = async (mode: 'pre' | 'post') => {
    if (!menuFund) return;
    handleMenuClose();
    setToast({ open: true, message: `Triggering ${mode}-market analysis for ${menuFund.name}...`, severity: 'info' });
    
    try {
        await generateReport(mode, menuFund.code);
        setToast({ open: true, message: `Task started! Check Reports page later.`, severity: 'success' });
    } catch (error) {
        setToast({ open: true, message: 'Failed to start analysis.', severity: 'error' });
        console.error(error);
    }
  };

  return (
    <div className="p-8 max-w-[1600px] mx-auto">
      {/* Header Section */}
      <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
           <Typography variant="h4" className="text-slate-900 font-bold tracking-tight mb-2">
              Fund Universe
           </Typography>
           <Typography variant="body1" className="text-slate-500">
              Active Portfolio Configuration
           </Typography>
        </div>
      </div>

      <Paper className="border border-slate-200 bg-white rounded-xl overflow-hidden shadow-sm">
        {/* Toolbar */}
        <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row gap-4 items-center bg-slate-50/50">
            <TextField
                placeholder="Search funds..."
                size="small"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                    startAdornment: <InputAdornment position="start"><SearchIcon className="text-slate-400" fontSize="small"/></InputAdornment>,
                }}
                className="w-full sm:w-80"
                sx={{ 
                    '& .MuiOutlinedInput-root': { bgcolor: '#ffffff' }
                }}
            />
            <div className="flex-grow" />
            <Button 
                variant="contained" 
                color="primary" 
                startIcon={<AddIcon />} 
                disableElevation
                onClick={() => handleOpenDialog()}
                className="bg-primary hover:bg-primary-dark text-white font-semibold"
            >
                Add Target
            </Button>
        </div>

        {/* Table */}
        <TableContainer sx={{ maxHeight: 'calc(100vh - 340px)' }}>
          <Table stickyHeader aria-label="sticky table">
            <TableHead>
              <TableRow>
                {headCells.map((headCell) => (
                  <TableCell
                    key={headCell.id}
                    align={headCell.align}
                    style={{ minWidth: headCell.minWidth }}
                    className="bg-slate-50 text-slate-500 font-mono text-xs tracking-wider border-b border-slate-200"
                  >
                    {headCell.label}
                  </TableCell>
                ))}
                <TableCell align="right" className="bg-slate-50 text-slate-500 font-mono text-xs tracking-wider border-b border-slate-200">
                    ACTIONS
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedFunds.map((row) => {
                return (
                  <TableRow hover role="checkbox" tabIndex={-1} key={row.code} className="hover:bg-slate-50 transition-colors">
                    <TableCell className="border-b border-slate-100">
                        <span className="font-mono text-primary font-bold bg-primary-DEFAULT/10 px-2 py-1 rounded">
                            {row.code}
                        </span>
                    </TableCell>
                    <TableCell className="border-b border-slate-100">
                        <Typography variant="body2" fontWeight={600} className="text-slate-700">
                            {row.name}
                        </Typography>
                    </TableCell>
                    <TableCell className="border-b border-slate-100">
                        {row.style ? (
                            <Chip label={row.style} size="small" variant="outlined" className="border-slate-300 text-slate-600 bg-white" />
                        ) : (
                            <span className="text-slate-400">-</span>
                        )}
                    </TableCell>
                    <TableCell className="border-b border-slate-100">
                        <div className="flex gap-1 flex-wrap">
                            {row.focus?.map((tag, idx) => (
                                <Chip key={idx} label={tag} size="small" className="bg-slate-100 text-slate-600 h-6 text-xs" />
                            ))}
                        </div>
                    </TableCell>
                    <TableCell className="border-b border-slate-100">
                        <div className="flex flex-col gap-1">
                            {row.pre_market_time && (
                                <div className="flex items-center gap-1.5 text-secondary-main">
                                    <ScheduleIcon sx={{ fontSize: 14 }} />
                                    <span className="text-xs font-mono font-bold">PRE: {row.pre_market_time}</span>
                                </div>
                            )}
                            {row.post_market_time && (
                                <div className="flex items-center gap-1.5 text-accent">
                                    <ScheduleIcon sx={{ fontSize: 14 }} />
                                    <span className="text-xs font-mono font-bold">POST: {row.post_market_time}</span>
                                </div>
                            )}
                            {!row.pre_market_time && !row.post_market_time && (
                                <span className="text-slate-400 text-xs italic">Manual Only</span>
                            )}
                        </div>
                    </TableCell>
                    <TableCell align="right" className="border-b border-slate-100">
                        <IconButton onClick={(e) => handleMenuOpen(e, row)} size="small" className="text-slate-400 hover:text-slate-700">
                            <MoreVertIcon fontSize="small" />
                        </IconButton>
                    </TableCell>
                  </TableRow>
                );
              })}
              {paginatedFunds.length === 0 && (
                  <TableRow>
                      <TableCell colSpan={6} align="center" sx={{ py: 8 }}>
                          <Typography color="text.secondary">No funds found matching your criteria.</Typography>
                      </TableCell>
                  </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[10, 25, 100]}
          component="div"
          count={filteredFunds.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          className="border-t border-slate-200 text-slate-500"
        />
      </Paper>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
            elevation: 2,
            sx: { minWidth: 200, bgcolor: '#ffffff', border: '1px solid #e2e8f0' }
        }}
      >
        <MenuItem onClick={() => handleRunAnalysis('pre')} className="hover:bg-slate-50">
            <ListItemIcon><AssessmentIcon fontSize="small" color="primary" /></ListItemIcon>
            <ListItemText className="text-slate-700">Run Pre-Market Now</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleRunAnalysis('post')} className="hover:bg-slate-50">
            <ListItemIcon><AssessmentIcon fontSize="small" className="text-accent" /></ListItemIcon>
            <ListItemText className="text-slate-700">Run Post-Market Now</ListItemText>
        </MenuItem>
        <Divider className="border-slate-100 my-1" />
        <MenuItem onClick={() => handleOpenDialog(menuFund!)} className="hover:bg-slate-50">
            <ListItemIcon><EditIcon fontSize="small" className="text-slate-500" /></ListItemIcon>
            <ListItemText className="text-slate-700">Edit Config</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleDelete(menuFund!.code)} className="hover:bg-slate-50">
            <ListItemIcon><DeleteIcon fontSize="small" color="error" /></ListItemIcon>
            <ListItemText sx={{ color: 'error.main' }}>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Dialog */}
      <Dialog 
        open={openDialog} 
        onClose={() => setOpenDialog(false)} 
        maxWidth="sm" 
        fullWidth
        PaperProps={{
            elevation: 4,
            sx: { borderRadius: 3, bgcolor: '#ffffff' }
        }}
      >
        <DialogTitle sx={{ 
            fontWeight: 700, 
            pb: 2,
            borderBottom: '1px solid #e2e8f0',
            color: '#0f172a'
        }}>
            {editingFund ? 'Edit Configuration' : 'Add New Target'}
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
            <div className="flex flex-col gap-6 mt-2">
                
                {/* Search Bar (Only for New Fund) */}
                {!editingFund && (
                    <Box>
                        <Typography variant="caption" className="text-slate-500 font-bold mb-2 block uppercase tracking-wider">
                            MARKET SEARCH
                        </Typography>
                        <Autocomplete
                            options={marketOptions}
                            getOptionLabel={(option) => `${option.code} ${option.name}`}
                            loading={searchLoading}
                            onInputChange={handleFundSearch}
                            onChange={handleFundSelect}
                            filterOptions={(x) => x}
                            renderOption={(props, option) => {
                                const { key, ...otherProps } = props;
                                return (
                                <li key={key} {...otherProps} className="hover:bg-slate-50">
                                    <div className="flex items-center w-full">
                                        <div className="flex-1">
                                            <Typography variant="body2" fontWeight={600} className="text-slate-700">
                                                {option.code}
                                            </Typography>
                                            <Typography variant="caption" className="text-slate-500">
                                                {option.name}
                                            </Typography>
                                        </div>
                                        <div>
                                            <Chip label={option.type} size="small" variant="outlined" className="border-slate-200 text-slate-500 text-[10px]" />
                                        </div>
                                    </div>
                                </li>
                                );
                            }}
                            renderInput={(params) => (
                                <TextField
                                    {...params}
                                    placeholder="Type fund code or name..."
                                    size="small"
                                    InputProps={{
                                        ...params.InputProps,
                                        endAdornment: (
                                            <>
                                                {searchLoading ? <CircularProgress color="inherit" size={20} /> : null}
                                                {params.InputProps.endAdornment}
                                            </>
                                        ),
                                    }}
                                />
                            )}
                        />
                    </Box>
                )}

                {/* Section: Basic Information */}
                <Box>
                    <Typography variant="caption" className="text-slate-500 font-bold mb-2 block uppercase tracking-wider">
                        ASSET DETAILS
                    </Typography>
                    <div className="flex gap-4">
                        <div className="w-1/3">
                            <TextField
                                label="Code"
                                fullWidth
                                value={formCode}
                                onChange={(e) => setFormCode(e.target.value)}
                                disabled={!!editingFund}
                                placeholder="000000"
                                size="small"
                            />
                        </div>
                        <div className="w-2/3">
                            <TextField
                                label="Name"
                                fullWidth
                                value={formName}
                                onChange={(e) => setFormName(e.target.value)}
                                placeholder="Fund Name"
                                size="small"
                            />
                        </div>
                    </div>
                </Box>

                {/* Section: Strategy */}
                <Box>
                    <Typography variant="caption" className="text-slate-500 font-bold mb-2 block uppercase tracking-wider">
                        STRATEGY TAGS
                    </Typography>
                    <div className="flex gap-4">
                        <div className="w-1/2">
                            <TextField
                                label="Style"
                                fullWidth
                                value={formStyle}
                                onChange={(e) => setFormStyle(e.target.value)}
                                placeholder="Growth, Value..."
                                size="small"
                            />
                        </div>
                        <div className="w-1/2">
                            <TextField
                                label="Sectors"
                                fullWidth
                                value={formFocus}
                                onChange={(e) => setFormFocus(e.target.value)}
                                placeholder="Tech, Medical..."
                                helperText="Comma separated"
                                size="small"
                            />
                        </div>
                    </div>
                </Box>

                {/* Section: Automation Schedule */}
                <div className="bg-slate-50 p-4 rounded-lg border border-dashed border-slate-300">
                    <div className="flex items-center mb-3">
                        <ScheduleIcon className="text-slate-400 mr-2" fontSize="small" />
                        <Typography variant="caption" className="text-slate-500 font-bold uppercase tracking-wider">
                            AUTOMATION (24H)
                        </Typography>
                    </div>
                    <div className="flex gap-4">
                        <div className="w-1/2">
                            <TextField
                                label="Pre-Market"
                                type="time"
                                fullWidth
                                value={formPreTime}
                                onChange={(e) => setFormPreTime(e.target.value)}
                                InputLabelProps={{ shrink: true }}
                                inputProps={{ step: 300 }} // 5 min steps
                                size="small"
                                sx={{ 
                                    '& input::-webkit-calendar-picker-indicator': { cursor: 'pointer' }
                                }}
                            />
                        </div>
                        <div className="w-1/2">
                            <TextField
                                label="Post-Market"
                                type="time"
                                fullWidth
                                value={formPostTime}
                                onChange={(e) => setFormPostTime(e.target.value)}
                                InputLabelProps={{ shrink: true }}
                                inputProps={{ step: 300 }}
                                size="small"
                                sx={{ 
                                    '& input::-webkit-calendar-picker-indicator': { cursor: 'pointer' }
                                }}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2.5, borderTop: '1px solid #e2e8f0' }}>
            <Button 
                onClick={() => setOpenDialog(false)} 
                className="text-slate-500 hover:text-slate-800"
            >
                Cancel
            </Button>
            <Button 
                onClick={handleSave} 
                variant="contained" 
                disableElevation 
                className="bg-primary hover:bg-primary-dark font-bold"
            >
                Confirm
            </Button>
        </DialogActions>
      </Dialog>

      <Snackbar 
        open={toast.open} 
        autoHideDuration={4000} 
        onClose={() => setToast({...toast, open: false})}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={toast.severity} sx={{ width: '100%' }}>
          {toast.message}
        </Alert>
      </Snackbar>
    </div>
  );
}
