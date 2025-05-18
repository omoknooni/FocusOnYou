// components/RequireAuth.jsx
import React, { useContext } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { CircularProgress, Box } from '@mui/material';

export default function RequireAuth({ children }) {
  const { user, loading } = useContext(AuthContext);
  const location = useLocation();

  if (loading) {
    // 세션 체크 중에는 로딩 표시
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!user) {
    // 인증 안 됐으면 로그인 페이지로
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
