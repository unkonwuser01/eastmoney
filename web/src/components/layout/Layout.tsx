import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { 
  Drawer, 
  List, 
  ListItem, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText, 
  Typography, 
} from '@mui/material';
import PieChartIcon from '@mui/icons-material/PieChart';
import ArticleIcon from '@mui/icons-material/Article';
import SettingsIcon from '@mui/icons-material/Settings';

const drawerWidth = 260;

const MENU_ITEMS = [
  { text: 'Universe', icon: <PieChartIcon />, path: '/funds' },
  { text: 'Intelligence', icon: <ArticleIcon />, path: '/reports' },
  { text: 'System', icon: <SettingsIcon />, path: '/settings' },
];

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="flex min-h-screen bg-background text-slate-900 font-sans">
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { 
            width: drawerWidth, 
            boxSizing: 'border-box',
            borderRight: '1px solid #e2e8f0', // Slate 200
            backgroundColor: '#ffffff', // White
          },
        }}
      >
        <div className="h-20 flex items-center px-6 border-b border-slate-200">
          <div className="flex flex-col">
            <Typography variant="h6" className="tracking-widest font-bold text-slate-900" sx={{ fontFamily: 'JetBrains Mono' }}>
              EASTMONEY
              <span className="text-primary-DEFAULT">.PRO</span>
            </Typography>
            <Typography variant="caption" className="text-slate-500 tracking-wider text-[0.65rem]">
              INTELLIGENCE TERMINAL
            </Typography>
          </div>
        </div>
        
        <div className="flex-1 py-6 px-3 overflow-y-auto">
          <List className="space-y-2">
            {MENU_ITEMS.map((item) => {
               const isActive = location.pathname.startsWith(item.path);
               return (
                <ListItem key={item.text} disablePadding>
                  <ListItemButton 
                    selected={isActive}
                    onClick={() => navigate(item.path)}
                    sx={{
                      borderRadius: '8px',
                      mb: 0.5,
                      '&.Mui-selected': {
                        backgroundColor: '#eff6ff', // Blue 50
                        borderLeft: '3px solid #2563eb', // Blue 600
                        '&:hover': { backgroundColor: '#dbeafe' }, // Blue 100
                      },
                      '&:hover': {
                        backgroundColor: '#f8fafc', // Slate 50
                      }
                    }}
                  >
                    <ListItemIcon sx={{ 
                      minWidth: 40, 
                      color: isActive ? '#2563eb' : '#64748b' 
                    }}>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText 
                      primary={item.text} 
                      primaryTypographyProps={{ 
                        fontWeight: isActive ? 600 : 500,
                        fontSize: '0.9rem',
                        color: isActive ? '#1e293b' : '#64748b'
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              );
            })}
          </List>
        </div>
      </Drawer>

      <main className="flex-grow bg-slate-50 p-0 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
