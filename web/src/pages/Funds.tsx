import { useState, useEffect, useMemo } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Container,
  TextField,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
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
  Tooltip,
  useTheme,
  alpha,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Snackbar,
  Alert
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AssessmentIcon from '@mui/icons-material/Assessment';
import { fetchFunds, saveFunds, generateReport,  } from '../api';
import type {FundItem} from '../api';
interface HeadCell {
  id: keyof FundItem;
  label: string;
  minWidth?: number;
  align?: 'left' | 'right' | 'center';
}

const headCells: HeadCell[] = [
  { id: 'code', label: 'Code', minWidth: 100 },
  { id: 'name', label: 'Fund Name', minWidth: 200 },
  { id: 'style', label: 'Strategy', minWidth: 120 },
  { id: 'focus', label: 'Focus Sectors', minWidth: 200 },
];

export default function FundsPage() {
  const theme = useTheme();
  const [funds, setFunds] = useState<FundItem[]>([]);
  const [loading, setLoading] = useState(false);
  
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
    setLoading(true);
    try {
      const data = await fetchFunds();
      setFunds(data);
    } catch (error) {
      console.error("Failed to load funds", error);
    } finally {
      setLoading(false);
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

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(+event.target.value);
    setPage(0);
  };

  // CRUD Handlers
  const handleOpenDialog = (fund?: FundItem) => {
    setAnchorEl(null); // Close menu if open
    if (fund) {
        setEditingFund(fund);
        setFormCode(fund.code);
        setFormName(fund.name);
        setFormStyle(fund.style || '');
        setFormFocus(fund.focus?.join(', ') || '');
    } else {
        setEditingFund(null);
        setFormCode('');
        setFormName('');
        setFormStyle('');
        setFormFocus('');
    }
    setOpenDialog(true);
  };

  const handleSave = async () => {
    const focusArray = formFocus.split(/[,，]/).map(s => s.trim()).filter(Boolean);
    
    const newFund: FundItem = {
        code: formCode,
        name: formName,
        style: formStyle,
        focus: focusArray
    };

    let updatedFunds = [...funds];
    if (editingFund) {
        updatedFunds = updatedFunds.map(f => f.code === editingFund.code ? newFund : f);
    } else {
        if (funds.some(f => f.code === newFund.code)) {
            alert("Fund with this code already exists!");
            return;
        }
        updatedFunds.push(newFund);
    }

    try {
        await saveFunds(updatedFunds);
        setFunds(updatedFunds);
        setOpenDialog(false);
        setToast({ open: true, message: 'Fund saved successfully', severity: 'success' });
    } catch (error) {
        setToast({ open: true, message: 'Failed to save fund', severity: 'error' });
    }
  };

  const handleDelete = async (code: string) => {
    setAnchorEl(null);
    if (!confirm("Delete this fund?")) return;
    try {
        const updatedFunds = funds.filter(f => f.code !== code);
        await saveFunds(updatedFunds);
        setFunds(updatedFunds);
        setToast({ open: true, message: 'Fund deleted', severity: 'success' });
    } catch (error) {
        setToast({ open: true, message: 'Failed to delete fund', severity: 'error' });
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
    setToast({ open: true, message: `Starting ${mode}-market analysis for ${menuFund.name}...`, severity: 'info' });
    
    try {
        await generateReport(mode, menuFund.code);
        setToast({ open: true, message: `Analysis complete! Check Reports.`, severity: 'success' });
    } catch (error) {
        setToast({ open: true, message: 'Analysis failed. Check console.', severity: 'error' });
        console.error(error);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" color="primary" sx={{ fontWeight: 700, mb: 1 }}>
            Fund Universe
        </Typography>
        <Typography variant="body1" color="text.secondary">
            Manage your asset portfolio configuration.
        </Typography>
      </Box>

      <Paper sx={{ width: '100%', overflow: 'hidden', border: `1px solid ${theme.palette.divider}` }}>
        {/* Table Toolbar */}
        <Box sx={{ p: 2, display: 'flex', gap: 2, alignItems: 'center', borderBottom: `1px solid ${theme.palette.divider}` }}>
            <TextField
                placeholder="Search..."
                size="small"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                    startAdornment: <InputAdornment position="start"><SearchIcon color="action" fontSize="small"/></InputAdornment>,
                }}
                sx={{ width: 300 }}
            />
            <Button startIcon={<FilterListIcon />} color="inherit" sx={{ color: 'text.secondary' }}>
                Filters
            </Button>
            <Box sx={{ flexGrow: 1 }} />
            <Button 
                variant="contained" 
                color="secondary" 
                startIcon={<AddIcon />} 
                disableElevation
                onClick={() => handleOpenDialog()}
            >
                Add Fund
            </Button>
        </Box>

        {/* Table Content */}
        <TableContainer sx={{ maxHeight: 'calc(100vh - 300px)' }}>
          <Table stickyHeader aria-label="sticky table">
            <TableHead>
              <TableRow>
                {headCells.map((headCell) => (
                  <TableCell
                    key={headCell.id}
                    align={headCell.align}
                    style={{ minWidth: headCell.minWidth, fontWeight: 600, backgroundColor: theme.palette.background.default }}
                  >
                    {headCell.label}
                  </TableCell>
                ))}
                <TableCell align="right" style={{ minWidth: 100, fontWeight: 600, backgroundColor: theme.palette.background.default }}>
                    Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedFunds.map((row) => {
                return (
                  <TableRow hover role="checkbox" tabIndex={-1} key={row.code}>
                    <TableCell>
                        <Chip 
                            label={row.code} 
                            size="small" 
                            sx={{ 
                                fontFamily: 'monospace', 
                                borderRadius: 1, 
                                bgcolor: alpha(theme.palette.primary.main, 0.05),
                                color: 'primary.main',
                                fontWeight: 700
                            }} 
                        />
                    </TableCell>
                    <TableCell>
                        <Typography variant="body2" fontWeight={500}>{row.name}</Typography>
                    </TableCell>
                    <TableCell>
                        {row.style ? (
                            <Chip label={row.style} size="small" variant="outlined" color="default" />
                        ) : (
                            <Typography variant="caption" color="text.secondary">-</Typography>
                        )}
                    </TableCell>
                    <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                            {row.focus?.map((tag, idx) => (
                                <Chip key={idx} label={tag} size="small" sx={{ height: 20, fontSize: '0.7rem' }} />
                            ))}
                        </Box>
                    </TableCell>
                    <TableCell align="right">
                        <IconButton onClick={(e) => handleMenuOpen(e, row)} size="small">
                            <MoreVertIcon fontSize="small" />
                        </IconButton>
                    </TableCell>
                  </TableRow>
                );
              })}
              {paginatedFunds.length === 0 && (
                  <TableRow>
                      <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
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
        />
      </Paper>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
            elevation: 3,
            sx: { minWidth: 200 }
        }}
      >
        <MenuItem onClick={() => handleRunAnalysis('pre')}>
            <ListItemIcon><AssessmentIcon fontSize="small" color="primary" /></ListItemIcon>
            <ListItemText>Run Pre-Market</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleRunAnalysis('post')}>
            <ListItemIcon><AssessmentIcon fontSize="small" color="secondary" /></ListItemIcon>
            <ListItemText>Run Post-Market</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => handleOpenDialog(menuFund!)}>
            <ListItemIcon><EditIcon fontSize="small" /></ListItemIcon>
            <ListItemText>Edit</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleDelete(menuFund!.code)}>
            <ListItemIcon><DeleteIcon fontSize="small" color="error" /></ListItemIcon>
            <ListItemText sx={{ color: 'error.main' }}>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 600 }}>
            {editingFund ? 'Edit Fund' : 'Add New Fund'}
        </DialogTitle>
        <DialogContent dividers>
            <Grid container spacing={2} sx={{ mt: 0.5 }}>
                <Grid item xs={12} sm={4}>
                    <TextField
                        autoFocus
                        label="Fund Code"
                        fullWidth
                        value={formCode}
                        onChange={(e) => setFormCode(e.target.value)}
                        disabled={!!editingFund}
                        placeholder="000000"
                        size="small"
                    />
                </Grid>
                <Grid item xs={12} sm={8}>
                    <TextField
                        label="Fund Name"
                        fullWidth
                        value={formName}
                        onChange={(e) => setFormName(e.target.value)}
                        placeholder="e.g. Blue Chip Growth"
                        size="small"
                    />
                </Grid>
                <Grid item xs={12} sm={6}>
                    <TextField
                        label="Strategy / Style"
                        fullWidth
                        value={formStyle}
                        onChange={(e) => setFormStyle(e.target.value)}
                        placeholder="e.g. Equity, Mix, ETF"
                        size="small"
                    />
                </Grid>
                <Grid item xs={12} sm={6}>
                    <TextField
                        label="Focus Sectors"
                        fullWidth
                        value={formFocus}
                        onChange={(e) => setFormFocus(e.target.value)}
                        helperText="Separate by comma (e.g. Tech, Gold)"
                        placeholder="Tech, Medical"
                        size="small"
                    />
                </Grid>
            </Grid>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
            <Button onClick={() => setOpenDialog(false)} color="inherit">Cancel</Button>
            <Button onClick={handleSave} variant="contained" disableElevation>Save</Button>
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
    </Container>
  );
}