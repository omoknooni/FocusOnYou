import { useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { CircularProgress, Box, Typography } from '@mui/material';

export default function Logout() {
  const { logout } = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        await logout();
      } finally {
        // 로그아웃 후 /login 페이지로 이동
        navigate('/login', { replace: true });
      }
    })();
  }, [logout, navigate]);

  // 로그아웃 처리 중에 간단한 로딩 UI
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 10 }}>
      <CircularProgress />
      <Typography sx={{ mt: 2 }}>로그아웃 처리 중입니다...</Typography>
    </Box>
  );
}
