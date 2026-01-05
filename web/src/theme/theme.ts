import { createTheme } from '@mui/material/styles';
import type {ThemeOptions} from '@mui/material/styles';
const themeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: '#0F172A', // Slate 900
    },
    secondary: {
      main: '#14B8A6', // Teal 500
      contrastText: '#ffffff',
    },
    background: {
      default: '#F8FAFC', // Slate 50
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1E293B', // Slate 800
      secondary: '#64748B', // Slate 500
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontWeight: 700, fontSize: '2rem' },
    h2: { fontWeight: 600, fontSize: '1.5rem' },
    h3: { fontWeight: 600, fontSize: '1.25rem' },
    h6: { fontWeight: 600 },
    subtitle1: { fontWeight: 500 },
    button: { textTransform: 'none', fontWeight: 600 },
    // Monospace for codes
    overline: { fontFamily: '"JetBrains Mono", "Roboto Mono", monospace' },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          boxShadow: '0px 1px 3px rgba(0, 0, 0, 0.1), 0px 1px 2px rgba(0, 0, 0, 0.06)', // Subtle shadow
          border: '1px solid #E2E8F0', // Slate 200
        },
        elevation0: {
          border: 'none',
          boxShadow: 'none',
        }
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          margin: '4px 8px',
          '&.Mui-selected': {
            backgroundColor: '#F1F5F9', // Slate 100
            borderLeft: '4px solid #0F172A',
            borderTopLeftRadius: 4,
            borderBottomLeftRadius: 4,
            paddingLeft: 12, // Compensate for border
            '&:hover': {
              backgroundColor: '#E2E8F0',
            }
          }
        }
      }
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          borderBottom: '1px solid #E2E8F0',
          backgroundColor: '#FFFFFF',
          color: '#0F172A'
        }
      }
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: '1px solid #E2E8F0',
          backgroundColor: '#FFFFFF',
        }
      }
    }
  },
};

export const theme = createTheme(themeOptions);
