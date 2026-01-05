import { useState, useEffect, useMemo } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  List, 
  ListItemButton, 
  ListItemText, 
  Chip,
  Button,
  CircularProgress,
  IconButton,
  Collapse,
  Divider,
  Stack,
  ListItemIcon
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import RefreshIcon from '@mui/icons-material/Refresh';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import ArticleIcon from '@mui/icons-material/Article';
import BusinessCenterIcon from '@mui/icons-material/BusinessCenter';
import ReactMarkdown from 'react-markdown';
import { fetchReports, fetchReportContent, generateReport,  } from '../api';
import type{ReportSummary} from '../api'
export default function ReportsPage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [selectedReport, setSelectedReport] = useState<ReportSummary | null>(null);
  const [reportContent, setReportContent] = useState<string>('');
  const [loadingContent, setLoadingContent] = useState<boolean>(false);
  const [generating, setGenerating] = useState<boolean>(false);
  
  // Grouping State
  const [expandedDates, setExpandedDates] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const data = await fetchReports();
      setReports(data);
      
      // Auto-expand the first date (newest)
      if (data.length > 0) {
          const newestDate = data[0].date;
          setExpandedDates(new Set([newestDate]));
          
          if (!selectedReport) {
             handleSelectReport(data[0]);
          }
      }
    } catch (error) {
      console.error("Failed to load reports", error);
    }
  };

  const handleSelectReport = async (report: ReportSummary) => {
    setSelectedReport(report);
    setLoadingContent(true);
    try {
      const content = await fetchReportContent(report.filename);
      setReportContent(content);
    } catch (error) {
      console.error("Failed to load content", error);
    } finally {
      setLoadingContent(false);
    }
  };

  const handleGenerate = async (mode: 'pre' | 'post') => {
    setGenerating(true);
    try {
      await generateReport(mode);
      await loadReports();
    } catch (error) {
        alert("Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const toggleDate = (date: string) => {
      const newSet = new Set(expandedDates);
      if (newSet.has(date)) {
          newSet.delete(date);
      } else {
          newSet.add(date);
      }
      setExpandedDates(newSet);
  };

  // Grouping Logic
  const groupedReports = useMemo(() => {
      const groups: Record<string, { overview: ReportSummary[], funds: ReportSummary[] }> = {};
      
      reports.forEach(r => {
          if (!groups[r.date]) {
              groups[r.date] = { overview: [], funds: [] };
          }
          if (r.is_summary) {
              groups[r.date].overview.push(r);
          } else {
              groups[r.date].funds.push(r);
          }
      });
      
      // Sort keys (dates) descending
      return Object.keys(groups).sort((a, b) => b.localeCompare(a)).map(date => ({
          date,
          ...groups[date]
      }));
  }, [reports]);

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
        {/* Left Sidebar: Hierarchical List */}
        <Box sx={{ 
            width: 320, 
            borderRight: '1px solid #E2E8F0', 
            bgcolor: 'background.paper',
            display: 'flex',
            flexDirection: 'column',
            flexShrink: 0
        }}>
            <Box sx={{ p: 2, borderBottom: '1px solid #E2E8F0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" fontWeight={600}>Library</Typography>
                <IconButton size="small" onClick={loadReports}><RefreshIcon /></IconButton>
            </Box>
            
            <Box sx={{ overflowY: 'auto', flex: 1 }}>
                <List component="nav">
                    {groupedReports.map((group) => (
                        <Box key={group.date}>
                            <ListItemButton onClick={() => toggleDate(group.date)} sx={{ bgcolor: '#F8FAFC', py: 1.5 }}>
                                <ListItemIcon sx={{ minWidth: 36 }}>
                                    <CalendarTodayIcon fontSize="small" color="action" />
                                </ListItemIcon>
                                <ListItemText 
                                    primary={group.date} 
                                    primaryTypographyProps={{ fontWeight: 600, fontSize: '0.9rem' }}
                                />
                                {expandedDates.has(group.date) ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
                            </ListItemButton>
                            
                            <Collapse in={expandedDates.has(group.date)} timeout="auto" unmountOnExit>
                                <List component="div" disablePadding>
                                    {/* Overview Reports */}
                                    {group.overview.map(report => (
                                        <ListItemButton 
                                            key={report.filename} 
                                            sx={{ pl: 4 }}
                                            selected={selectedReport?.filename === report.filename}
                                            onClick={() => handleSelectReport(report)}
                                        >
                                            <ListItemIcon sx={{ minWidth: 30 }}>
                                                <ArticleIcon fontSize="small" color={report.mode === 'pre' ? 'primary' : 'secondary'} />
                                            </ListItemIcon>
                                            <ListItemText 
                                                primary={report.mode === 'pre' ? 'Pre-Market Overview' : 'Post-Market Overview'}
                                                primaryTypographyProps={{ fontSize: '0.85rem' }}
                                            />
                                        </ListItemButton>
                                    ))}

                                    {/* Individual Funds Header */}
                                    {group.funds.length > 0 && (
                                        <Box>
                                            <Typography variant="caption" sx={{ pl: 4, py: 1, display: 'block', color: 'text.secondary', fontWeight: 600 }}>
                                                INDIVIDUAL ASSETS ({group.funds.length})
                                            </Typography>
                                            {group.funds.map(report => (
                                                <ListItemButton 
                                                    key={report.filename} 
                                                    sx={{ pl: 4 }}
                                                    selected={selectedReport?.filename === report.filename}
                                                    onClick={() => handleSelectReport(report)}
                                                >
                                                    <ListItemIcon sx={{ minWidth: 30 }}>
                                                        <BusinessCenterIcon fontSize="small" sx={{ opacity: 0.7 }} />
                                                    </ListItemIcon>
                                                    <ListItemText 
                                                        primary={report.fund_name}
                                                        secondary={
                                                            <Stack direction="row" spacing={1} alignItems="center" mt={0.5}>
                                                                <Chip 
                                                                    label={report.fund_code} 
                                                                    size="small" 
                                                                    sx={{ height: 16, fontSize: '0.65rem' }} 
                                                                />
                                                                <Typography variant="caption" color={report.mode === 'pre' ? 'primary.main' : 'secondary.main'} fontWeight={600}>
                                                                    {report.mode.toUpperCase()}
                                                                </Typography>
                                                            </Stack>
                                                        }
                                                        primaryTypographyProps={{ fontSize: '0.85rem' }}
                                                    />
                                                </ListItemButton>
                                            ))}
                                        </Box>
                                    )}
                                </List>
                            </Collapse>
                            <Divider />
                        </Box>
                    ))}
                    {reports.length === 0 && (
                        <Box sx={{ p: 4, textAlign: 'center', color: 'text.secondary' }}>
                            <Typography variant="body2">No reports found.</Typography>
                        </Box>
                    )}
                </List>
            </Box>
        </Box>

        {/* Right Content: Detail */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', minWidth: 0 }}>
            {/* Toolbar */}
            <Box sx={{ 
                p: 2, 
                borderBottom: '1px solid #E2E8F0', 
                bgcolor: 'white',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexShrink: 0
            }}>
                <Box>
                    {selectedReport && (
                        <Box>
                            <Typography variant="subtitle1" fontWeight={600}>
                                {selectedReport.is_summary ? 'Market Overview' : selectedReport.fund_name}
                            </Typography>
                            <Stack direction="row" spacing={1} alignItems="center">
                                <Chip 
                                    label={selectedReport.date} 
                                    size="small" 
                                    variant="outlined" 
                                    sx={{ height: 20, fontSize: '0.7rem' }} 
                                />
                                <Chip 
                                    label={selectedReport.mode === 'pre' ? 'Pre-Market' : 'Post-Market'} 
                                    size="small" 
                                    color={selectedReport.mode === 'pre' ? 'primary' : 'secondary'}
                                    sx={{ height: 20, fontSize: '0.7rem' }} 
                                />
                                {!selectedReport.is_summary && (
                                    <Chip label={selectedReport.fund_code} size="small" sx={{ height: 20, fontSize: '0.7rem', fontFamily: 'monospace' }} />
                                )}
                            </Stack>
                        </Box>
                    )}
                </Box>
                <Stack direction="row" spacing={2}>
                    <Button 
                        variant="outlined" 
                        startIcon={generating ? <CircularProgress size={16} /> : <PlayArrowIcon />}
                        onClick={() => handleGenerate('pre')}
                        disabled={generating}
                    >
                        Run Pre-Market
                    </Button>
                    <Button 
                        variant="contained" 
                        color="secondary"
                        disableElevation
                        startIcon={generating ? <CircularProgress size={16} color="inherit" /> : <PlayArrowIcon />}
                        onClick={() => handleGenerate('post')}
                        disabled={generating}
                    >
                        Run Post-Market
                    </Button>
                </Stack>
            </Box>

            {/* Content Area */}
            <Box sx={{ flex: 1, overflowY: 'auto', p: 5, bgcolor: '#FAFAFA' }}>
                {loadingContent ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}>
                        <CircularProgress />
                    </Box>
                ) : selectedReport ? (
                    <Paper sx={{ maxWidth: 800, mx: 'auto', p: 6, minHeight: '80vh' }}>
                        <div className="markdown-body">
                            <ReactMarkdown>{reportContent}</ReactMarkdown>
                        </div>
                    </Paper>
                ) : (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'text.secondary' }}>
                        <Typography>Select a report to view details</Typography>
                    </Box>
                )}
            </Box>
        </Box>
    </Box>
  );
}