import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function Upload() {
  const [faceName, setFaceName] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async e => {
    e.preventDefault();
    if (!faceName || !imageFile || !videoFile) {
      alert('모든 항목을 입력하세요');
      return;
    }
    // 1. Create job
    const { data } = await api.post('/jobs/create', {
      face_name: faceName,
      image_filename: imageFile.name,
      image_filetype: imageFile.type,
      video_filename: videoFile.name,
      video_filetype: videoFile.type,
    });

    // 2. Upload files
    await api.put(data.presigned_urls.image.url, imageFile, {
      headers: { 'Content-Type': imageFile.type },
    });
    await api.put(data.presigned_urls.video.url, videoFile, {
      headers: { 'Content-Type': videoFile.type },
    });

    // 3. Navigate to detail
    navigate(`/jobs/${data.job_id}`);
  };

  return (
    <form onSubmit={handleSubmit} className="upload-form">
      <h2>Upload Photo & Video</h2>
      <input
        type="text"
        placeholder="Face Name"
        value={faceName}
        onChange={e => setFaceName(e.target.value)}
        required
      />
      <input
        type="file"
        accept="image/*"
        onChange={e => setImageFile(e.target.files[0])}
        required
      />
      <input
        type="file"
        accept="video/*"
        onChange={e => setVideoFile(e.target.files[0])}
        required
      />
      <button type="submit">Start Job</button>
    </form>
  );
}
