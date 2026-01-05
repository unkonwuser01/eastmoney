import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Container,
  TextField,
  Button,
  Grid,
  CircularProgress,
  Snackbar,
  Alert,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  InputAdornment,
  Stack,
  MenuItem,
  useTheme
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import KeyIcon from '@mui/icons-material/Key';
import PsychologyIcon from '@mui/icons-material/Psychology';
import LanguageIcon from '@mui/icons-material/Language';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { fetchSettings, saveSettings,  } from '../api';
import type{SettingsData}from '../api';
export default function SettingsPage() {
  const theme = useTheme();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<SettingsData>({
    llm_provider: 'gemini',
    gemini_api_key_masked: '',
    openai_api_key_masked: '',
    tavily_api_key_masked: ''
  });
  
  // Inputs (separate from masked state to allow editing)
  const [geminiKey, setGeminiKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [tavilyKey, setTavilyKey] = useState('');
  
  const [toast, setToast] = useState<{open: boolean, message: string, severity: 'success'|'error'}>({
    open: false, message: '', severity: 'success'
  });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const data = await fetchSettings();
      setSettings(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
        await saveSettings({
            llm_provider: settings.llm_provider,
            gemini_api_key: geminiKey || undefined, // Only send if changed
            openai_api_key: openaiKey || undefined,
            tavily_api_key: tavilyKey || undefined
        });
        setToast({ open: true, message: 'Configuration saved successfully', severity: 'success' });
        // Clear inputs and reload to show masked
        setGeminiKey('');
        setOpenaiKey('');
        setTavilyKey('');
        await loadSettings();
    } catch (error) {
        setToast({ open: true, message: 'Failed to save configuration', severity: 'error' });
    } finally {
        setSaving(false);
    }
  };

  if (loading) return (
      <Box sx={{ height: '80vh', display:'flex', justifyContent:'center', alignItems: 'center' }}>
          <CircularProgress />
      </Box>
  );

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      {/* Header */}
      <Box sx={{ mb: 6, textAlign: 'center' }}>
        <Typography variant="h4" fontWeight={800} color="primary" gutterBottom>
            System Configuration
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
            Manage your AI intelligence providers and external data connections. 
            Keys are stored securely in your local environment.
        </Typography>
      </Box>

      <Stack spacing={4}>
        {/* LLM Engine Section */}
        <Card variant="outlined" sx={{ overflow: 'visible' }}>
            <CardHeader 
                avatar={
                    <Box sx={{ bgcolor: 'primary.light', p: 1, borderRadius: 2, color: 'primary.main' }}>
                        <PsychologyIcon fontSize="large" />
                    </Box>
                }
                title={<Typography variant="h6" fontWeight={700}>Intelligence Engine</Typography>}
                subheader="Select and configure the Large Language Model driving the analysis."
                sx={{ pb: 0 }}
            />
            <CardContent sx={{ p: 4 }}>
                <Grid container spacing={4}>
                    <Grid item xs={12}>
                         <TextField 
                            fullWidth 
                            label="Active Provider" 
                            value={settings.llm_provider}
                            onChange={(e) => setSettings({...settings, llm_provider: e.target.value})}
                            select 
                            variant="outlined"
                            helperText="Choose the AI model used for report generation."
                        >
                            <MenuItem value="gemini">Google Gemini (Recommended)</MenuItem>
                            <MenuItem value="openai">OpenAI (GPT-4)</MenuItem>
                        </TextField>
                    </Grid>
                    
                    <Grid item xs={12}>
                        <Divider sx={{ mb: 2 }}>
                            <Chip label="Credentials" size="small" />
                        </Divider>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <TextField 
                            fullWidth 
                            label="Gemini API Key"
                            type="password" 
                            placeholder={settings.gemini_api_key_masked || "Enter AIza..."}
                            value={geminiKey}
                            onChange={(e) => setGeminiKey(e.target.value)}
                            helperText={settings.gemini_api_key_masked ? "Key is configured" : "Required for Gemini provider"}
                            InputProps={{
                                startAdornment: <InputAdornment position="start"><KeyIcon color="action" fontSize="small"/></InputAdornment>,
                                endAdornment: settings.gemini_api_key_masked && !geminiKey && (
                                    <InputAdornment position="end"><CheckCircleIcon color="success" fontSize="small"/></InputAdornment>
                                )
                            }}
                            disabled={settings.llm_provider !== 'gemini' && !geminiKey}
                        />
                    </Grid>
                    <Grid item xs={12} md={6}>
                         <TextField 
                            fullWidth 
                            label="OpenAI API Key"
                            type="password" 
                            placeholder={settings.openai_api_key_masked || "Enter sk-..."}
                            value={openaiKey}
                            onChange={(e) => setOpenaiKey(e.target.value)}
                            helperText={settings.openai_api_key_masked ? "Key is configured" : "Required for OpenAI provider"}
                            InputProps={{
                                startAdornment: <InputAdornment position="start"><KeyIcon color="action" fontSize="small"/></InputAdornment>,
                                endAdornment: settings.openai_api_key_masked && !openaiKey && (
                                    <InputAdornment position="end"><CheckCircleIcon color="success" fontSize="small"/></InputAdornment>
                                )
                            }}
                            disabled={settings.llm_provider !== 'openai' && !openaiKey}
                        />
                    </Grid>
                </Grid>
            </CardContent>
        </Card>

        {/* Data Sources Section */}
        <Card variant="outlined">
            <CardHeader 
                avatar={
                    <Box sx={{ bgcolor: 'secondary.light', p: 1, borderRadius: 2, color: 'secondary.main' }}>
                        <LanguageIcon fontSize="large" />
                    </Box>
                }
                title={<Typography variant="h6" fontWeight={700}>Data Connections</Typography>}
                subheader="Configure external services for web search and market data."
                sx={{ pb: 0 }}
            />
            <CardContent sx={{ p: 4 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12}>
                        <Alert severity="info" icon={<InfoOutlinedIcon />} sx={{ mb: 3, bgcolor: 'background.default' }}>
                            A Tavily API key is required to perform real-time web searches for news and sentiment analysis.
                        </Alert>
                        <TextField 
                            fullWidth 
                            label="Tavily Search API Key" 
                            type="password"
                            placeholder={settings.tavily_api_key_masked || "Enter tvly-..."}
                            value={tavilyKey}
                            onChange={(e) => setTavilyKey(e.target.value)}
                            InputProps={{
                                startAdornment: <InputAdornment position="start"><KeyIcon color="action" fontSize="small"/></InputAdornment>,
                                endAdornment: settings.tavily_api_key_masked && !tavilyKey && (
                                    <InputAdornment position="end"><CheckCircleIcon color="success" fontSize="small"/></InputAdornment>
                                )
                            }}
                        />
                    </Grid>
                </Grid>
            </CardContent>
        </Card>

        {/* Action Area */}
        <Box sx={{ display: 'flex', justifyContent: 'center', pt: 2 }}>
             <Button 
                variant="contained" 
                size="large"
                startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />} 
                onClick={handleSave}
                disabled={saving}
                sx={{ 
                    px: 6, 
                    py: 1.5, 
                    borderRadius: 2,
                    fontSize: '1.1rem',
                    textTransform: 'none',
                    fontWeight: 700,
                    boxShadow: '0 4px 14px 0 rgba(0,0,0,0.1)'
                }}
            >
                {saving ? 'Saving Changes...' : 'Save Configuration'}
            </Button>
        </Box>
      </Stack>

      <Snackbar 
        open={toast.open} 
        autoHideDuration={4000} 
        onClose={() => setToast({...toast, open: false})}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={toast.severity} sx={{ width: '100%', borderRadius: 2 }}>
          {toast.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}
