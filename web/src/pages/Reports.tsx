import { useState, useEffect, useMemo, useRef } from 'react';
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
    ListItemIcon,
    TextField,
    InputAdornment,
    Avatar,
    useTheme,
    Tooltip
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import RefreshIcon from '@mui/icons-material/Refresh';
import DownloadIcon from '@mui/icons-material/Download';
import html2canvas from 'html2canvas';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import ArticleIcon from '@mui/icons-material/Article';
import BusinessCenterIcon from '@mui/icons-material/BusinessCenter';
import SearchIcon from '@mui/icons-material/Search';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import ReactMarkdown from 'react-markdown';
import { fetchReports, fetchReportContent, generateReport } from '../api';
import type { ReportSummary } from '../api'

// Styled components or custom styles
const reportPaperStyle = {
    maxWidth: 900,
    mx: 'auto',
    minHeight: '80vh',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
    borderRadius: 2
};

const markdownStyles = {
    '& h1': { fontSize: '1.8rem', fontWeight: 700, color: '#1e293b', mb: 2, borderBottom: '1px solid #e2e8f0', pb: 1 },
    '& h2': { fontSize: '1.4rem', fontWeight: 600, color: '#334155', mt: 4, mb: 2 },
    '& h3': { fontSize: '1.1rem', fontWeight: 600, color: '#475569', mt: 3, mb: 1.5 },
    '& p': { fontSize: '1.05rem', lineHeight: 1.7, color: '#374151', mb: 2, fontFamily: '"Georgia", "Times New Roman", serif' },
    '& ul, & ol': { mb: 2, pl: 3 },
    '& li': { mb: 0.5, lineHeight: 1.6, fontFamily: '"Georgia", "Times New Roman", serif' },
    '& strong': { color: '#111827', fontWeight: 600 },
    '& blockquote': { borderLeft: '4px solid #3b82f6', pl: 2, py: 0.5, my: 2, bgcolor: '#eff6ff', borderRadius: '0 4px 4px 0', fontStyle: 'italic' },
    '& table': { width: '100%', borderCollapse: 'collapse', mb: 3, mt: 2 },
    '& th': { borderBottom: '2px solid #e2e8f0', textAlign: 'left', p: 1, fontWeight: 600, color: '#475569' },
    '& td': { borderBottom: '1px solid #e2e8f0', p: 1, color: '#374151' }
};

export default function ReportsPage() {
    const theme = useTheme();
    const [reports, setReports] = useState<ReportSummary[]>([]);
    const [selectedReport, setSelectedReport] = useState<ReportSummary | null>(null);
    const [reportContent, setReportContent] = useState<string>('');
    const [loadingContent, setLoadingContent] = useState<boolean>(false);
    const [exporting, setExporting] = useState<boolean>(false);

    // Ref for export
    const reportRef = useRef<HTMLDivElement>(null);

    // Search State
    const [searchQuery, setSearchQuery] = useState('');

    // Grouping State
    const [expandedDates, setExpandedDates] = useState<Set<string>>(new Set());
    const [expandedFunds, setExpandedFunds] = useState<Set<string>>(new Set());

    useEffect(() => {
        loadReports();
    }, []);

    const loadReports = async () => {
        try {
            const data = await fetchReports();
            setReports(data);

            // Auto-expand the first date
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

    const toggleDate = (date: string) => {
        const newSet = new Set(expandedDates);
        if (newSet.has(date)) newSet.delete(date);
        else newSet.add(date);
        setExpandedDates(newSet);
    };

    const toggleFund = (fundKey: string) => {
        const newSet = new Set(expandedFunds);
        if (newSet.has(fundKey)) newSet.delete(fundKey);
        else newSet.add(fundKey);
        setExpandedFunds(newSet);
    };

    // Export report as image
    const handleExportImage = async () => {
        if (!reportRef.current || !selectedReport) return;
        
        setExporting(true);
        try {
            // 设置固定宽度以获得更好的导出效果
            const exportWidth = 1200; // 固定导出宽度，接近页面显示宽度
            const originalWidth = reportRef.current.style.width;
            const originalMaxWidth = reportRef.current.style.maxWidth;
            
            // 临时设置宽度
            reportRef.current.style.width = `${exportWidth}px`;
            reportRef.current.style.maxWidth = `${exportWidth}px`;
            
            const canvas = await html2canvas(reportRef.current, {
                scale: 2, // Higher quality
                useCORS: true,
                backgroundColor: '#ffffff',
                logging: false,
                width: exportWidth,
                windowWidth: exportWidth
            });
            
            // 恢复原始样式
            reportRef.current.style.width = originalWidth;
            reportRef.current.style.maxWidth = originalMaxWidth;
            
            // Convert to image and download
            const link = document.createElement('a');
            const fileName = `${selectedReport.fund_name || 'report'}_${selectedReport.mode}_${selectedReport.date}.png`;
            link.download = fileName.replace(/[^a-zA-Z0-9_\-一-龥]/g, '_');
            link.href = canvas.toDataURL('image/png');
            link.click();
        } catch (error) {
            console.error('Failed to export image:', error);
        } finally {
            setExporting(false);
        }
    };

    // Advanced Grouping Logic: Search -> Date -> Fund -> Report
    const groupedData = useMemo(() => {
        // 1. Filter
        const filtered = reports.filter(r => {
            const q = searchQuery.toLowerCase();
            return (
                r.date.includes(q) ||
                (r.fund_name && r.fund_name.toLowerCase().includes(q)) ||
                (r.fund_code && r.fund_code.includes(q))
            );
        });

        // 2. Group by Date
        const dateGroups: Record<string, { overview: ReportSummary[], funds: Record<string, ReportSummary[]> }> = {};

        filtered.forEach(r => {
            if (!dateGroups[r.date]) {
                dateGroups[r.date] = { overview: [], funds: {} };
            }

            if (r.is_summary) {
                dateGroups[r.date].overview.push(r);
            } else {
                const fundKey = `${r.fund_name}|${r.fund_code}`;
                if (!dateGroups[r.date].funds[fundKey]) {
                    dateGroups[r.date].funds[fundKey] = [];
                }
                dateGroups[r.date].funds[fundKey].push(r);
            }
        });

        // 3. Convert to Array and Sort
        return Object.keys(dateGroups).sort((a, b) => b.localeCompare(a)).map(date => {
            const group = dateGroups[date];
            const fundList = Object.keys(group.funds).map(key => {
                const [name, code] = key.split('|');
                return {
                    key,
                    name,
                    code,
                    reports: group.funds[key].sort((a, b) => (a.mode === 'pre' ? -1 : 1)) // Pre first
                };
            });

            return {
                date,
                overviews: group.overview,
                funds: fundList
            };
        });
    }, [reports, searchQuery]);

    return (
        <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: '#F1F5F9' }}>
            {/* Sidebar */}
            <Box sx={{
                width: 340,
                borderRight: '1px solid #E2E8F0',
                bgcolor: '#FFFFFF',
                display: 'flex',
                flexDirection: 'column',
                flexShrink: 0,
                zIndex: 10
            }}>
                {/* Header & Search */}
                <Box sx={{ p: 2, borderBottom: '1px solid #E2E8F0' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6" fontWeight={700} color="text.primary">Intelligence Library</Typography>
                        <IconButton size="small" onClick={loadReports}><RefreshIcon /></IconButton>
                    </Box>
                    <TextField
                        fullWidth
                        size="small"
                        placeholder="Search reports..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        InputProps={{
                            startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" color="action" /></InputAdornment>,
                        }}
                        sx={{ '& .MuiOutlinedInput-root': { bgcolor: '#F8FAFC' } }}
                    />
                </Box>

                {/* Hierarchical List */}
                <Box sx={{ overflowY: 'auto', flex: 1, '&::-webkit-scrollbar': { width: '6px' }, '&::-webkit-scrollbar-thumb': { bgcolor: '#CBD5E1' } }}>
                    <List component="nav" disablePadding>
                        {groupedData.map((group) => (
                            <Box key={group.date}>
                                {/* Level 1: Date */}
                                <ListItemButton onClick={() => toggleDate(group.date)} sx={{ bgcolor: '#F8FAFC', py: 1.5, borderBottom: '1px solid #F1F5F9' }}>
                                    <ListItemIcon sx={{ minWidth: 32 }}>
                                        <CalendarTodayIcon fontSize="small" sx={{ fontSize: 18, color: '#64748B' }} />
                                    </ListItemIcon>
                                    <ListItemText
                                        primary={group.date}
                                        primaryTypographyProps={{ fontWeight: 600, fontSize: '0.85rem', color: '#334155' }}
                                    />
                                    {expandedDates.has(group.date) ? <ExpandLess fontSize="small" sx={{ color: '#94A3B8' }} /> : <ExpandMore fontSize="small" sx={{ color: '#94A3B8' }} />}
                                </ListItemButton>

                                <Collapse in={expandedDates.has(group.date)} timeout="auto" unmountOnExit>
                                    <List component="div" disablePadding>

                                        {/* Level 2: Overviews (Directly listed) */}
                                        {group.overviews.map(report => (
                                            <ListItemButton
                                                key={report.filename}
                                                sx={{ pl: 6, borderLeft: selectedReport?.filename === report.filename ? '4px solid #3b82f6' : '4px solid transparent' }}
                                                selected={selectedReport?.filename === report.filename}
                                                onClick={() => handleSelectReport(report)}
                                            >
                                                <ListItemIcon sx={{ minWidth: 28 }}>
                                                    <ArticleIcon fontSize="small" sx={{ fontSize: 18, color: report.mode === 'pre' ? '#3b82f6' : '#f59e0b' }} />
                                                </ListItemIcon>
                                                <ListItemText
                                                    primary={report.mode === 'pre' ? 'Daily Market Briefing' : 'Market Wrap-up'}
                                                    secondary={report.mode === 'pre' ? 'Pre-Market' : 'Post-Market'}
                                                    primaryTypographyProps={{ fontSize: '0.85rem', fontWeight: 500 }}
                                                    secondaryTypographyProps={{ fontSize: '0.7rem' }}
                                                />
                                            </ListItemButton>
                                        ))}

                                        {/* Level 2: Funds Group */}
                                        {group.funds.map(fund => {
                                            const isFundExpanded = expandedFunds.has(`${group.date}-${fund.key}`);
                                            return (
                                                <Box key={fund.key}>
                                                    <ListItemButton
                                                        onClick={() => toggleFund(`${group.date}-${fund.key}`)}
                                                        sx={{ pl: 4, py: 1 }}
                                                    >
                                                        <ListItemIcon sx={{ minWidth: 28 }}>
                                                            <BusinessCenterIcon fontSize="small" sx={{ fontSize: 18, color: '#94A3B8' }} />
                                                        </ListItemIcon>
                                                        <ListItemText
                                                            primary={fund.name}
                                                            secondary={fund.code}
                                                            primaryTypographyProps={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}
                                                            secondaryTypographyProps={{ fontSize: '0.7rem', fontFamily: 'monospace' }}
                                                        />
                                                        {isFundExpanded ? <ExpandLess fontSize="small" sx={{ fontSize: 16, color: '#CBD5E1' }} /> : <ExpandMore fontSize="small" sx={{ fontSize: 16, color: '#CBD5E1' }} />}
                                                    </ListItemButton>

                                                    {/* Level 3: Fund Reports */}
                                                    <Collapse in={isFundExpanded} timeout="auto" unmountOnExit>
                                                        <List component="div" disablePadding>
                                                            {fund.reports.map(report => (
                                                                <ListItemButton
                                                                    key={report.filename}
                                                                    sx={{
                                                                        pl: 8,
                                                                        py: 1,
                                                                        borderLeft: selectedReport?.filename === report.filename ? '4px solid #3b82f6' : '4px solid transparent',
                                                                        bgcolor: selectedReport?.filename === report.filename ? '#eff6ff' : 'transparent'
                                                                    }}
                                                                    selected={selectedReport?.filename === report.filename}
                                                                    onClick={() => handleSelectReport(report)}
                                                                >
                                                                    <ListItemIcon sx={{ minWidth: 24 }}>
                                                                        {report.mode === 'pre' ?
                                                                            <TrendingUpIcon sx={{ fontSize: 16, color: '#3b82f6' }} /> :
                                                                            <TrendingDownIcon sx={{ fontSize: 16, color: '#f59e0b' }} />
                                                                        }
                                                                    </ListItemIcon>
                                                                    <ListItemText
                                                                        primary={report.mode === 'pre' ? 'Pre-Market Strategy' : 'Post-Market Review'}
                                                                        primaryTypographyProps={{ fontSize: '0.8rem' }}
                                                                    />
                                                                </ListItemButton>
                                                            ))}
                                                        </List>
                                                    </Collapse>
                                                </Box>
                                            );
                                        })}
                                    </List>
                                </Collapse>
                            </Box>
                        ))}
                    </List>
                </Box>
            </Box>

            {/* Right Content: Professional Report View */}
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
                {/* Export Button Bar */}
                {selectedReport && (
                    <Box sx={{ p: 2, bgcolor: '#FFFFFF', borderBottom: '1px solid #E2E8F0', display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                        <Tooltip title="导出为长图片">
                            <Button
                                variant="outlined"
                                size="small"
                                startIcon={exporting ? <CircularProgress size={16} /> : <DownloadIcon />}
                                onClick={handleExportImage}
                                disabled={exporting || loadingContent}
                                sx={{ borderRadius: 2 }}
                            >
                                {exporting ? '导出中...' : '导出图片'}
                            </Button>
                        </Tooltip>
                    </Box>
                )}
                <Box sx={{ flex: 1, overflowY: 'auto', p: 4 }}>
                    {selectedReport ? (
                        <Paper sx={reportPaperStyle} ref={reportRef}>
                            {/* Report Header */}
                            <Box sx={{
                                p: 5,
                                bgcolor: 'white',
                                borderBottom: '1px solid #E2E8F0',
                                backgroundImage: 'linear-gradient(to right, #ffffff, #f8fafc)'
                            }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <Box>
                                        <Typography variant="overline" color="text.secondary" fontWeight={600} letterSpacing={1.2}>
                                            {selectedReport.is_summary ? 'MARKET INTELLIGENCE' : 'FUND ANALYSIS REPORT'}
                                        </Typography>
                                        <Typography variant="h4" fontWeight={800} sx={{ mt: 1, mb: 1, color: '#1e293b' }}>
                                            {selectedReport.is_summary ? 'Daily Market Overview' : selectedReport.fund_name}
                                        </Typography>
                                        {!selectedReport.is_summary && (
                                            <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                                                <Typography variant="h6" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                                                    {selectedReport.fund_code}
                                                </Typography>
                                            </Stack>
                                        )}
                                    </Box>
                                    <Chip
                                        icon={<AccessTimeIcon />}
                                        label={selectedReport.date}
                                        sx={{ bgcolor: '#F1F5F9', fontWeight: 600, color: '#475569' }}
                                    />
                                </Box>

                                <Stack direction="row" spacing={1} mt={3}>
                                    <Chip
                                        label={selectedReport.mode === 'pre' ? 'PRE-MARKET' : 'POST-MARKET'}
                                        color={selectedReport.mode === 'pre' ? 'primary' : 'warning'}
                                        size="small"
                                        sx={{ fontWeight: 700, borderRadius: 1 }}
                                    />
                                </Stack>
                            </Box>

                            {/* Report Body */}
                            <Box sx={{ p: 6, flex: 1, bgcolor: '#FFFFFF' }}>
                                {loadingContent ? (
                                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
                                        <CircularProgress size={30} thickness={4} />
                                    </Box>
                                ) : (
                                    <Box sx={markdownStyles} className="markdown-body">
                                        <ReactMarkdown>{reportContent}</ReactMarkdown>
                                    </Box>
                                )}
                            </Box>

                            {/* Footer */}
                            <Box sx={{ p: 3, bgcolor: '#F8FAFC', borderTop: '1px solid #E2E8F0', textAlign: 'center' }}>
                                <Typography variant="caption" color="text.secondary">
                                    Generated by Deep Data Mining System • Confidential • {new Date().getFullYear()}
                                </Typography>
                            </Box>
                        </Paper>
                    ) : (
                        <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'text.secondary' }}>
                            <BusinessCenterIcon sx={{ fontSize: 60, opacity: 0.2, mb: 2 }} />
                            <Typography variant="h6" color="text.disabled">Select a report to view analysis</Typography>
                        </Box>
                    )}
                </Box>
            </Box>
        </Box>
    );
}