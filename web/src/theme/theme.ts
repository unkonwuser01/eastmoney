import { createTheme } from '@mui/material/styles';
import type { ThemeOptions } from '@mui/material/styles';

const themeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: '#2563eb', // Blue 600
      light: '#60a5fa',
      dark: '#1e40af',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#0d9488', // Teal 600
      contrastText: '#ffffff',
    },
    background: {
      default: '#f8fafc', // Slate 50
      paper: '#ffffff',   // White
    },
    text: {
      primary: '#0f172a', // Slate 900
      secondary: '#64748b', // Slate 500
    },
    divider: '#e2e8f0', // Slate 200
    action: {
      hover: 'rgba(0, 0, 0, 0.04)',
      selected: 'rgba(37, 99, 235, 0.08)', // Primary tint
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontWeight: 700, letterSpacing: '-0.025em', color: '#0f172a' },
    h2: { fontWeight: 700, letterSpacing: '-0.025em', color: '#0f172a' },
    h3: { fontWeight: 600, letterSpacing: '-0.025em', color: '#0f172a' },
    h4: { fontWeight: 600, letterSpacing: '-0.025em', color: '#0f172a' },
    h6: { fontWeight: 600, color: '#0f172a' },
    subtitle1: { fontWeight: 500, color: '#334155' },
    button: { textTransform: 'none', fontWeight: 600, borderRadius: 8 },
    overline: { fontFamily: '"JetBrains Mono", monospace', letterSpacing: '0.1em' },
    body1: { lineHeight: 1.7, color: '#334155' },
    body2: { color: '#475569' },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#f8fafc',
          scrollbarColor: '#cbd5e1 transparent',
          '&::-webkit-scrollbar, & *::-webkit-scrollbar': {
            width: '8px',
            height: '8px',
          },
          '&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb': {
            borderRadius: 8,
            backgroundColor: '#cbd5e1',
            minHeight: 24,
            border: '2px solid transparent',
            backgroundClip: 'content-box',
          },
          '&::-webkit-scrollbar-thumb:focus, & *::-webkit-scrollbar-thumb:focus': {
            backgroundColor: '#94a3b8',
          },
          '&::-webkit-scrollbar-thumb:hover, & *::-webkit-scrollbar-thumb:hover': {
            backgroundColor: '#94a3b8',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          },
        },
        containedPrimary: {
          background: '#2563eb',
          '&:hover': {
             background: '#1d4ed8',
          }
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)', // Tailwind shadow-sm
          border: '1px solid #e2e8f0',
        },
        elevation0: {
            boxShadow: 'none',
            border: 'none'
        }
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#ffffff',
          borderRight: '1px solid #e2e8f0',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          borderBottom: '1px solid #e2e8f0',
          color: '#0f172a',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid #e2e8f0',
          color: '#334155',
        },
        head: {
          color: '#64748b',
          fontWeight: 600,
          backgroundColor: '#f8fafc',
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: '#e2e8f0',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: '#cbd5e1',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: '#2563eb',
            boxShadow: '0 0 0 3px rgba(37, 99, 235, 0.1)',
          },
        },
        input: {
            color: '#0f172a',
        }
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
        },
        filled: {
          backgroundColor: '#f1f5f9', // Slate 100
          color: '#334155',
        },
        outlined: {
            borderColor: '#cbd5e1',
            color: '#475569',
        }
      },
    },
    MuiMenu: {
        styleOverrides: {
            paper: {
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                border: '1px solid #e2e8f0',
            }
        }
    },
    MuiDialog: {
        styleOverrides: {
            paper: {
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                border: '1px solid #e2e8f0',
            }
        }
    }
  },
};

export const theme = createTheme(themeOptions);
