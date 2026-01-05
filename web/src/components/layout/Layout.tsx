import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { 
  Box, 
  Drawer, 
  List, 
  ListItem, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText, 
  Typography, 
  Divider,
  Toolbar
} from '@mui/material';
import PieChartIcon from '@mui/icons-material/PieChart';
import ArticleIcon from '@mui/icons-material/Article';
import SettingsIcon from '@mui/icons-material/Settings';

const drawerWidth = 260;

const MENU_ITEMS = [
  { text: 'Reports', icon: <ArticleIcon />, path: '/reports' },
  { text: 'Fund Universe', icon: <PieChartIcon />, path: '/funds' },
  { text: 'System', icon: <SettingsIcon />, path: '/settings' },
];

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Box sx={{ display: 'flex' }}>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { 
            width: drawerWidth, 
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar sx={{ px: 3 }}>
          <Typography variant="h6" color="primary" sx={{ fontWeight: 700 }}>
            EastMoney Pro
          </Typography>
        </Toolbar>
        <Divider />
        <Box sx={{ overflow: 'auto', mt: 2 }}>
          <List>
            {MENU_ITEMS.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton 
                  selected={location.pathname.startsWith(item.path)}
                  onClick={() => navigate(item.path)}
                >
                  <ListItemIcon sx={{ minWidth: 40, color: location.pathname.startsWith(item.path) ? 'secondary.main' : 'text.secondary' }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText 
                    primary={item.text} 
                    primaryTypographyProps={{ fontWeight: 500 }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
        <Box sx={{ mt: 'auto', p: 2 }}>
            <Typography variant="caption" color="text.secondary" display="block" align="center">
                Gemini: <span style={{color: '#14B8A6'}}>Connected</span>
            </Typography>
        </Box>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, bgcolor: 'background.default', minHeight: '100vh', p: 0 }}>
         {/* No Top App Bar by default, unless page needs it. Padding handled by pages or container */}
        <Outlet />
      </Box>
    </Box>
  );
}
