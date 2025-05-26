import React, { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Grid,
  Alert,
  LinearProgress,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import axios from 'axios';

export default function Upload() {
  const [faceName, setFaceName] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!faceName || !imageFile || !videoFile) {
      setError('모든 항목을 입력해주세요.');
      return;
    }

    const MAX_IMAGE_SIZE = 5 * 1024 * 1024;
    const MAX_VIDEO_SIZE = 300 * 1024 * 1024;
    if (imageFile.size > MAX_IMAGE_SIZE || videoFile.size > MAX_VIDEO_SIZE) {
      setError('파일 크기는 300MB를 초과할 수 없습니다.');
      return;
    }

    setLoading(true);
    try {
      // 1. Create job
      const { data } = await api.post('/jobs/create', {
        face_name: faceName,
        image_filename: imageFile.name,
        image_filetype: imageFile.type,
        video_filename: videoFile.name,
        video_filetype: videoFile.type,
      });

      // 2. Upload files
      // await api.put(data.presigned_urls.image.url, imageFile, {
      //   headers: { 'Content-Type': imageFile.type },
      // });
      const formData = new FormData();
      Object.entries(data.presigned_data.image.fields).forEach(([key, value]) => {
        formData.append(key, value);
      });
      formData.append('file', imageFile);

      await axios.post(data.presigned_data.image.url, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // await api.put(data.presigned_urls.video.url, videoFile, {
      //   headers: { 'Content-Type': videoFile.type },
      // });
      const videoFormData = new FormData();
      Object.entries(data.presigned_data.video.fields).forEach(([key, value]) => {
        videoFormData.append(key, value);
      });

      await axios.post(data.presigned_data.video.url, videoFormData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // 3. Navigate to detail
      navigate(`/jobs/${data.job_id}`);
    } catch (err) {
      setError('업로드 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="sm">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Typography component="h1" variant="h5">
          파일 업로드
        </Typography>

        {error && (
          <Alert severity="error" sx={{ width: '100%', mt: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 3 }}>
          <TextField
            fullWidth
            required
            id="faceName"
            label="Face Name"
            name="faceName"
            value={faceName}
            onChange={(e) => setFaceName(e.target.value)}
          />

          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={12} sm={6}>
              <Button
                variant="outlined"
                component="label"
                fullWidth
              >
                사진 선택
                <input
                  type="file"
                  accept="image/*"
                  hidden
                  onChange={(e) => setImageFile(e.target.files[0])}
                />
              </Button>
              {imageFile && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  선택된 사진: {imageFile.name}
                </Typography>
              )}
            </Grid>

            <Grid item xs={12} sm={6}>
              <Button
                variant="outlined"
                component="label"
                fullWidth
              >
                비디오 선택
                <input
                  type="file"
                  accept="video/*"
                  hidden
                  onChange={(e) => setVideoFile(e.target.files[0])}
                />
              </Button>
              {videoFile && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  선택된 비디오: {videoFile.name}
                </Typography>
              )}
            </Grid>
          </Grid>

          {loading && <LinearProgress sx={{ mt: 3 }} />}

          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={loading}
          >
            {loading ? '업로드 중...' : 'Start Job'}
          </Button>
        </Box>
      </Box>
    </Container>
  );
}
