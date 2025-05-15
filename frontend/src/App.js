import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline, Container } from '@mui/material';
import NavBar from './components/NavBar';
import Home from './pages/Home';
import Login from './pages/Login';
import Upload from './pages/Upload';
import JobsList from './pages/JobsList';
import JobDetail from './pages/JobDetail';
import { AuthProvider } from './contexts/AuthContext';
import './App.css';

// Material-UI 테마 생성
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <NavBar />
        <Container sx={{ mt: 4, mb: 4 }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/jobs" element={<JobsList />} />
            <Route path="/jobs/:jobId" element={<JobDetail />} />
          </Routes>
        </Container>
      </AuthProvider>
    </ThemeProvider>
  );
}
