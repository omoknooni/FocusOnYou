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
import RequireAuth from './components/RequireAuth';
import Logout from './components/Logout';
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
            <Route path="/logout" element={<Logout />} />
            {/* 인증된 사용자만 접근 가능 */}
            <Route
              path="/upload"
              element={
                <RequireAuth>
                  <Upload />
                </RequireAuth>
              }
            />
            <Route
              path="/jobs"
              element={
                <RequireAuth>
                  <JobsList />
                </RequireAuth>
              }
            />
            <Route
              path="/jobs/:jobId"
              element={
                <RequireAuth>
                  <JobDetail />
                </RequireAuth>
              }
            />
          </Routes>
        </Container>
      </AuthProvider>
    </ThemeProvider>
  );
}
