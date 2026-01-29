import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Typography, 
  TextField,
  Button,
  CircularProgress,
  Snackbar,
  Alert,
  Card,
  CardContent,
  Chip,
  Divider,
  InputAdornment,
  MenuItem,
  Autocomplete,
  Switch,
  FormControlLabel,
  FormGroup,
  Tabs,
  Tab,
  Box,
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import KeyIcon from '@mui/icons-material/Key';
import PsychologyIcon from '@mui/icons-material/Psychology';
import LanguageIcon from '@mui/icons-material/Language';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import RefreshIcon from '@mui/icons-material/Refresh';
import EmailIcon from '@mui/icons-material/Email';
import SendIcon from '@mui/icons-material/Send';
import NotificationsIcon from '@mui/icons-material/Notifications';
import ScheduleIcon from '@mui/icons-material/Schedule';
import { fetchSettings, saveSettings, fetchLLMModels, fetchNotificationSettings, saveNotificationSettings, sendTestEmail } from '../api';
import type { SettingsData, NotificationSettingsData } from '../api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function SettingsPage() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<SettingsData>({
    llm_provider: 'gemini',
    gemini_api_key_masked: '',
    openai_api_key_masked: '',
    tavily_api_key_masked: ''
  });
  
  // Inputs
  const [geminiKey, setGeminiKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [tavilyKey, setTavilyKey] = useState('');
  const [openaiBaseUrl, setOpenaiBaseUrl] = useState('');
  const [openaiModel, setOpenaiModel] = useState('');
  
  // Models
  const [modelList, setModelList] = useState<string[]>([]);
  const [fetchingModels, setFetchingModels] = useState(false);
  
  // Notification Settings
  const [notificationSettings, setNotificationSettings] = useState<NotificationSettingsData>({
    email_enabled: false,
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_password_masked: '',
    smtp_from_email: '',
    smtp_use_tls: true,
    recipient_email: '',
    notify_on_report: true,
    notify_on_alert: true,
    notify_daily_summary: false,
    quiet_hours_enabled: false,
    quiet_hours_start: '22:00',
    quiet_hours_end: '08:00',
    daily_summary_time: '18:00',
  });
  const [smtpPassword, setSmtpPassword] = useState('');
  const [sendingTestEmail, setSendingTestEmail] = useState(false);
  const [savingNotifications, setSavingNotifications] = useState(false);
  
  // Tab state
  const [activeTab, setActiveTab] = useState(0);
  
  const [toast, setToast] = useState<{open: boolean, message: string, severity: 'success'|'error'}>({
    open: false, message: '', severity: 'success'
  });

  useEffect(() => {
    loadSettings();
    loadNotificationSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const data = await fetchSettings();
      setSettings(data);
      setOpenaiBaseUrl(data.openai_base_url || '');
      setOpenaiModel(data.openai_model || '');
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const loadNotificationSettings = async () => {
    try {
      const data = await fetchNotificationSettings();
      setNotificationSettings(data);
    } catch (error) {
      console.error('Failed to load notification settings:', error);
    }
  };

  const handleFetchModels = async () => {
    setFetchingModels(true);
    try {
        const res = await fetchLLMModels(
            settings.llm_provider, 
            openaiKey || undefined, 
            openaiBaseUrl || undefined
        );
        setModelList(res.models);
        if (res.models.length > 0) {
             setToast({ open: true, message: `Found ${res.models.length} models`, severity: 'success' });
             // Only auto-select if empty
             if (!openaiModel) setOpenaiModel(res.models[0]);
        } else {
             setToast({ open: true, message: 'No models returned', severity: 'error' });
        }
    } catch (error: any) {
        setToast({ open: true, message: 'Failed to fetch models: ' + (error.response?.data?.detail || error.message), severity: 'error' });
    } finally {
        setFetchingModels(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
        await saveSettings({
            llm_provider: settings.llm_provider,
            gemini_api_key: geminiKey || undefined,
            openai_api_key: openaiKey || undefined,
            openai_base_url: openaiBaseUrl || undefined,
            openai_model: openaiModel || undefined,
            tavily_api_key: tavilyKey || undefined
        });
        setToast({ open: true, message: t('settings.messages.success'), severity: 'success' });
        setGeminiKey('');
        setOpenaiKey('');
        setTavilyKey('');
        await loadSettings();
    } catch (error) {
        setToast({ open: true, message: t('settings.messages.fail'), severity: 'error' });
    } finally {
        setSaving(false);
    }
  };

  const handleSaveNotifications = async () => {
    setSavingNotifications(true);
    try {
      await saveNotificationSettings({
        email_enabled: notificationSettings.email_enabled,
        smtp_host: notificationSettings.smtp_host || undefined,
        smtp_port: notificationSettings.smtp_port || undefined,
        smtp_user: notificationSettings.smtp_user || undefined,
        smtp_password: smtpPassword || undefined,
        smtp_from_email: notificationSettings.smtp_from_email || undefined,
        smtp_use_tls: notificationSettings.smtp_use_tls,
        recipient_email: notificationSettings.recipient_email || undefined,
        notify_on_report: notificationSettings.notify_on_report,
        notify_on_alert: notificationSettings.notify_on_alert,
        notify_daily_summary: notificationSettings.notify_daily_summary,
        quiet_hours_enabled: notificationSettings.quiet_hours_enabled,
        quiet_hours_start: notificationSettings.quiet_hours_start || undefined,
        quiet_hours_end: notificationSettings.quiet_hours_end || undefined,
        daily_summary_time: notificationSettings.daily_summary_time || undefined,
      });
      setToast({ open: true, message: t('settings.notifications.messages.success'), severity: 'success' });
      setSmtpPassword('');
      await loadNotificationSettings();
    } catch (error) {
      setToast({ open: true, message: t('settings.notifications.messages.fail'), severity: 'error' });
    } finally {
      setSavingNotifications(false);
    }
  };

  const handleSendTestEmail = async () => {
    setSendingTestEmail(true);
    try {
      const result = await sendTestEmail(notificationSettings.recipient_email);
      setToast({ open: true, message: result.message || t('settings.notifications.test_success'), severity: 'success' });
    } catch (error: any) {
      setToast({ open: true, message: error.response?.data?.detail || t('settings.notifications.test_fail'), severity: 'error' });
    } finally {
      setSendingTestEmail(false);
    }
  };

  if (loading) return (
      <div className="h-[80vh] flex justify-center items-center">
          <CircularProgress />
      </div>
  );

  return (
    <div className="max-w-4xl mx-auto py-12 px-6">
      {/* Header */}
      <div className="mb-8 text-center">
        <Typography
          variant="h4"
          align="center"
          sx={{ textAlign: 'center' }}
          className="text-slate-900 font-extrabold tracking-tight mb-2"
        >
            {t('settings.title')}
        </Typography>
        <Typography
          variant="body1"
          align="center"
          sx={{
            textAlign: 'center',
            display: 'block',
            maxWidth: '36rem',
            marginLeft: 'auto',
            marginRight: 'auto',
          }}
          className="text-slate-500"
        >
            {t('settings.subtitle')}
        </Typography>
      </div>

      {/* Tabs */}
      <Card variant="outlined" className="bg-white border-slate-200 shadow-sm">
        <Tabs 
          value={activeTab} 
          onChange={(_, newValue) => setActiveTab(newValue)}
          variant="fullWidth"
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              py: 2,
              fontWeight: 600,
            }
          }}
        >
          <Tab 
            icon={<PsychologyIcon />} 
            iconPosition="start" 
            label={t('settings.llm.title')} 
          />
          <Tab 
            icon={<LanguageIcon />} 
            iconPosition="start" 
            label={t('settings.data.title')} 
          />
          <Tab 
            icon={<EmailIcon />} 
            iconPosition="start" 
            label={t('settings.notifications.title')} 
          />
        </Tabs>

        {/* Tab 0: LLM Engine */}
        <TabPanel value={activeTab} index={0}>
          <CardContent className="p-6 md:p-8">
            <div className="grid grid-cols-1 gap-6">
              <div>
                <TextField 
                  fullWidth 
                  label={t('settings.llm.provider')}
                  value={settings.llm_provider}
                  onChange={(e) => setSettings({...settings, llm_provider: e.target.value})}
                  select 
                  variant="outlined"
                  helperText={t('settings.llm.provider_help')}
                  sx={{ '& .MuiOutlinedInput-root': { bgcolor: '#ffffff' } }}
                >
                  <MenuItem value="gemini">Google Gemini (Recommended)</MenuItem>
                  <MenuItem value="openai">OpenAI (GPT-4)</MenuItem>
                  <MenuItem value="openai_compatible">OpenAI Compatible (Custom)</MenuItem>
                </TextField>
              </div>
              
              <div>
                <Divider className="border-slate-200 mb-2">
                  <Chip label={t('settings.llm.credentials')} size="small" className="bg-slate-100 text-slate-500 font-mono text-xs uppercase tracking-wider" />
                </Divider>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <TextField 
                  fullWidth 
                  label={t('settings.llm.gemini_key')}
                  type="password" 
                  placeholder={settings.gemini_api_key_masked || "Enter AIza..."}
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  helperText={settings.gemini_api_key_masked ? "Key is configured" : "Required for Gemini provider"}
                  InputProps={{
                    startAdornment: <InputAdornment position="start"><KeyIcon className="text-slate-400" fontSize="small"/></InputAdornment>,
                    endAdornment: settings.gemini_api_key_masked && !geminiKey && (
                      <InputAdornment position="end"><CheckCircleIcon color="success" fontSize="small"/></InputAdornment>
                    )
                  }}
                  disabled={settings.llm_provider !== 'gemini' && !geminiKey}
                />
                <TextField 
                  fullWidth 
                  label={t('settings.llm.openai_key')}
                  type="password" 
                  placeholder={settings.openai_api_key_masked || "Enter sk-..."}
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  helperText={settings.openai_api_key_masked ? "Key is configured" : "Required for OpenAI provider"}
                  InputProps={{
                    startAdornment: <InputAdornment position="start"><KeyIcon className="text-slate-400" fontSize="small"/></InputAdornment>,
                    endAdornment: settings.openai_api_key_masked && !openaiKey && (
                      <InputAdornment position="end"><CheckCircleIcon color="success" fontSize="small"/></InputAdornment>
                    )
                  }}
                  disabled={settings.llm_provider !== 'openai' && settings.llm_provider !== 'openai_compatible' && !openaiKey}
                />
              </div>

              {(settings.llm_provider === 'openai' || settings.llm_provider === 'openai_compatible') && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                  <TextField 
                    fullWidth 
                    label={t('settings.llm.base_url') || "API Base URL"}
                    placeholder="https://api.openai.com/v1"
                    value={openaiBaseUrl}
                    onChange={(e) => setOpenaiBaseUrl(e.target.value)}
                    helperText="Override default OpenAI endpoint"
                  />
                  <div className="flex gap-2 items-start">
                    <Autocomplete
                      freeSolo
                      fullWidth
                      options={modelList}
                      value={openaiModel}
                      onInputChange={(_, newValue) => setOpenaiModel(newValue)}
                      renderInput={(params) => (
                        <TextField 
                          {...params}
                          label={t('settings.llm.model') || "Model Name"}
                          placeholder="gpt-4o"
                          helperText="e.g. gpt-4o, deepseek-chat"
                        />
                      )}
                    />
                    <Button 
                      variant="outlined" 
                      sx={{ height: 56, minWidth: 56 }}
                      onClick={handleFetchModels}
                      disabled={fetchingModels || (!openaiKey && !settings.openai_api_key_masked && !openaiBaseUrl)}
                      title="Fetch Models"
                    >
                      {fetchingModels ? <CircularProgress size={24} /> : <RefreshIcon />}
                    </Button>
                  </div>
                </div>
              )}

              {/* Save Button */}
              <div className="flex justify-end mt-4">
                <Button 
                  variant="contained" 
                  size="large"
                  startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />} 
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? t('settings.saving') : t('settings.save')}
                </Button>
              </div>
            </div>
          </CardContent>
        </TabPanel>

        {/* Tab 1: Data Sources */}
        <TabPanel value={activeTab} index={1}>
          <CardContent className="p-6 md:p-8">
            <div className="grid grid-cols-1 gap-6">
              <Alert severity="info" icon={<InfoOutlinedIcon />} className="bg-blue-50 text-blue-800 border border-blue-100">
                {t('settings.data.tavily_info')}
              </Alert>
              <TextField 
                fullWidth 
                label={t('settings.data.tavily_key')}
                type="password"
                placeholder={settings.tavily_api_key_masked || "Enter tvly-..."}
                value={tavilyKey}
                onChange={(e) => setTavilyKey(e.target.value)}
                InputProps={{
                  startAdornment: <InputAdornment position="start"><KeyIcon className="text-slate-400" fontSize="small"/></InputAdornment>,
                  endAdornment: settings.tavily_api_key_masked && !tavilyKey && (
                    <InputAdornment position="end"><CheckCircleIcon color="success" fontSize="small"/></InputAdornment>
                  )
                }}
              />

              {/* Save Button */}
              <div className="flex justify-end mt-4">
                <Button 
                  variant="contained" 
                  size="large"
                  startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />} 
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? t('settings.saving') : t('settings.save')}
                </Button>
              </div>
            </div>
          </CardContent>
        </TabPanel>

        {/* Tab 2: Email Notifications */}
        <TabPanel value={activeTab} index={2}>
          <CardContent className="p-6 md:p-8">
            <div className="grid grid-cols-1 gap-6">
              {/* Master Switch */}
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div>
                  <Typography variant="subtitle1" className="font-semibold text-slate-900">
                    {t('settings.notifications.title')}
                  </Typography>
                  <Typography variant="body2" className="text-slate-500">
                    {t('settings.notifications.subtitle')}
                  </Typography>
                </div>
                <FormControlLabel
                  control={
                    <Switch 
                      checked={notificationSettings.email_enabled}
                      onChange={(e) => setNotificationSettings({...notificationSettings, email_enabled: e.target.checked})}
                      color="primary"
                    />
                  }
                  label={notificationSettings.email_enabled ? t('settings.notifications.enabled') : t('settings.notifications.disabled')}
                  labelPlacement="start"
                />
              </div>

              {/* SMTP Configuration */}
              <div>
                <Divider className="border-slate-200 mb-4">
                  <Chip label={t('settings.notifications.smtp.title')} size="small" className="bg-slate-100 text-slate-500 font-mono text-xs uppercase tracking-wider" />
                </Divider>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <TextField 
                  fullWidth 
                  label={t('settings.notifications.smtp.host')}
                  placeholder="smtp.gmail.com"
                  value={notificationSettings.smtp_host}
                  onChange={(e) => setNotificationSettings({...notificationSettings, smtp_host: e.target.value})}
                  disabled={!notificationSettings.email_enabled}
                  helperText={t('settings.notifications.smtp.host_help')}
                />
                <div className="grid grid-cols-2 gap-4">
                  <TextField 
                    fullWidth 
                    label={t('settings.notifications.smtp.port')}
                    type="number"
                    value={notificationSettings.smtp_port}
                    onChange={(e) => setNotificationSettings({...notificationSettings, smtp_port: parseInt(e.target.value) || 587})}
                    disabled={!notificationSettings.email_enabled}
                  />
                  <FormControlLabel
                    control={
                      <Switch 
                        checked={notificationSettings.smtp_use_tls}
                        onChange={(e) => setNotificationSettings({...notificationSettings, smtp_use_tls: e.target.checked})}
                        disabled={!notificationSettings.email_enabled}
                      />
                    }
                    label="TLS"
                    className="mt-2"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <TextField 
                  fullWidth 
                  label={t('settings.notifications.smtp.user')}
                  placeholder="your@email.com"
                  value={notificationSettings.smtp_user}
                  onChange={(e) => setNotificationSettings({...notificationSettings, smtp_user: e.target.value})}
                  disabled={!notificationSettings.email_enabled}
                />
                <TextField 
                  fullWidth 
                  label={t('settings.notifications.smtp.password')}
                  type="password"
                  placeholder={notificationSettings.smtp_password_masked || t('settings.notifications.smtp.password_placeholder')}
                  value={smtpPassword}
                  onChange={(e) => setSmtpPassword(e.target.value)}
                  disabled={!notificationSettings.email_enabled}
                  InputProps={{
                    startAdornment: <InputAdornment position="start"><KeyIcon className="text-slate-400" fontSize="small"/></InputAdornment>,
                    endAdornment: notificationSettings.smtp_password_masked && !smtpPassword && (
                      <InputAdornment position="end"><CheckCircleIcon color="success" fontSize="small"/></InputAdornment>
                    )
                  }}
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <TextField 
                  fullWidth 
                  label={t('settings.notifications.smtp.from_email')}
                  placeholder="noreply@yourdomain.com"
                  value={notificationSettings.smtp_from_email}
                  onChange={(e) => setNotificationSettings({...notificationSettings, smtp_from_email: e.target.value})}
                  disabled={!notificationSettings.email_enabled}
                  helperText={t('settings.notifications.smtp.from_help')}
                />
                <TextField 
                  fullWidth 
                  label={t('settings.notifications.recipient')}
                  placeholder="you@email.com"
                  value={notificationSettings.recipient_email}
                  onChange={(e) => setNotificationSettings({...notificationSettings, recipient_email: e.target.value})}
                  disabled={!notificationSettings.email_enabled}
                  helperText={t('settings.notifications.recipient_help')}
                />
              </div>

              {/* Feature Toggles */}
              <div className="mt-4">
                <Divider className="border-slate-200 mb-4">
                  <Chip 
                    icon={<NotificationsIcon fontSize="small" />}
                    label={t('settings.notifications.triggers.title')} 
                    size="small" 
                    className="bg-slate-100 text-slate-500 font-mono text-xs uppercase tracking-wider" 
                  />
                </Divider>
              </div>
              
              <FormGroup row className="gap-4">
                <FormControlLabel
                  control={
                    <Switch 
                      checked={notificationSettings.notify_on_report}
                      onChange={(e) => setNotificationSettings({...notificationSettings, notify_on_report: e.target.checked})}
                      disabled={!notificationSettings.email_enabled}
                    />
                  }
                  label={t('settings.notifications.triggers.on_report')}
                />
                <FormControlLabel
                  control={
                    <Switch 
                      checked={notificationSettings.notify_on_alert}
                      onChange={(e) => setNotificationSettings({...notificationSettings, notify_on_alert: e.target.checked})}
                      disabled={!notificationSettings.email_enabled}
                    />
                  }
                  label={t('settings.notifications.triggers.on_alert')}
                />
                <FormControlLabel
                  control={
                    <Switch 
                      checked={notificationSettings.notify_daily_summary}
                      onChange={(e) => setNotificationSettings({...notificationSettings, notify_daily_summary: e.target.checked})}
                      disabled={!notificationSettings.email_enabled}
                    />
                  }
                  label={t('settings.notifications.triggers.daily_summary')}
                />
              </FormGroup>

              {/* Timing Settings */}
              <div className="mt-4">
                <Divider className="border-slate-200 mb-4">
                  <Chip 
                    icon={<ScheduleIcon fontSize="small" />}
                    label={t('settings.notifications.timing.title')} 
                    size="small" 
                    className="bg-slate-100 text-slate-500 font-mono text-xs uppercase tracking-wider" 
                  />
                </Divider>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <FormControlLabel
                  control={
                    <Switch 
                      checked={notificationSettings.quiet_hours_enabled}
                      onChange={(e) => setNotificationSettings({...notificationSettings, quiet_hours_enabled: e.target.checked})}
                      disabled={!notificationSettings.email_enabled}
                    />
                  }
                  label={t('settings.notifications.timing.quiet_hours')}
                />
                <TextField 
                  fullWidth 
                  label={t('settings.notifications.timing.quiet_start')}
                  type="time"
                  value={notificationSettings.quiet_hours_start}
                  onChange={(e) => setNotificationSettings({...notificationSettings, quiet_hours_start: e.target.value})}
                  disabled={!notificationSettings.email_enabled || !notificationSettings.quiet_hours_enabled}
                  InputLabelProps={{ shrink: true }}
                />
                <TextField 
                  fullWidth 
                  label={t('settings.notifications.timing.quiet_end')}
                  type="time"
                  value={notificationSettings.quiet_hours_end}
                  onChange={(e) => setNotificationSettings({...notificationSettings, quiet_hours_end: e.target.value})}
                  disabled={!notificationSettings.email_enabled || !notificationSettings.quiet_hours_enabled}
                  InputLabelProps={{ shrink: true }}
                />
              </div>

              {notificationSettings.notify_daily_summary && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div></div>
                  <TextField 
                    fullWidth 
                    label={t('settings.notifications.timing.summary_time')}
                    type="time"
                    value={notificationSettings.daily_summary_time}
                    onChange={(e) => setNotificationSettings({...notificationSettings, daily_summary_time: e.target.value})}
                    disabled={!notificationSettings.email_enabled}
                    InputLabelProps={{ shrink: true }}
                    helperText={t('settings.notifications.timing.summary_help')}
                  />
                  <div></div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-4 justify-end mt-4">
                <Button 
                  variant="outlined" 
                  startIcon={sendingTestEmail ? <CircularProgress size={18} /> : <SendIcon />}
                  onClick={handleSendTestEmail}
                  disabled={!notificationSettings.email_enabled || !notificationSettings.smtp_host || !notificationSettings.recipient_email || sendingTestEmail}
                >
                  {t('settings.notifications.test_button')}
                </Button>
                <Button 
                  variant="contained" 
                  startIcon={savingNotifications ? <CircularProgress size={18} color="inherit" /> : <SaveIcon />}
                  onClick={handleSaveNotifications}
                  disabled={savingNotifications}
                >
                  {savingNotifications ? t('settings.saving') : t('settings.notifications.save_button')}
                </Button>
              </div>
            </div>
          </CardContent>
        </TabPanel>
      </Card>

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
    </div>
  );
}