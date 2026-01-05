import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export interface ReportSummary {
  filename: string;
  date: string;
  mode: 'pre' | 'post';
  fund_code?: string;
  fund_name?: string;
  is_summary: boolean;
}

export const fetchReports = async (): Promise<ReportSummary[]> => {
  const response = await axios.get(`${API_BASE}/reports`);
  return response.data;
};

export const fetchReportContent = async (filename: string): Promise<string> => {
  const response = await axios.get(`${API_BASE}/reports/${filename}`);
  return response.data.content;
};

export const generateReport = async (mode: 'pre' | 'post', fundCode?: string): Promise<void> => {
  await axios.post(`${API_BASE}/generate/${mode}`, { fund_code: fundCode });
};

export interface FundItem {
  code: string;
  name: string;
  style?: string;
  focus?: string[];
}

export interface SettingsData {
  llm_provider: string;
  gemini_api_key_masked: string;
  openai_api_key_masked: string;
  tavily_api_key_masked: string;
}

export interface SettingsUpdate {
  llm_provider?: string;
  gemini_api_key?: string;
  openai_api_key?: string;
  tavily_api_key?: string;
}

export const fetchFunds = async (): Promise<FundItem[]> => {
  const response = await axios.get(`${API_BASE}/funds`);
  return response.data;
};

export const saveFunds = async (funds: FundItem[]): Promise<void> => {
  await axios.post(`${API_BASE}/funds`, funds);
};

export const fetchSettings = async (): Promise<SettingsData> => {
  const response = await axios.get(`${API_BASE}/settings`);
  return response.data;
};

export const saveSettings = async (settings: SettingsUpdate): Promise<void> => {
  await axios.post(`${API_BASE}/settings`, settings);
};
