import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../services/api';

export default function JobDetail() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);

  useEffect(() => {
    api.get(`/jobs/${jobId}`).then(res => setJob(res.data));
  }, [jobId]);

  if (!job) return <p>Loading...</p>;

  return (
    <div>
      <h2>Job Detail: {job.job_id}</h2>
      <ul>
        <li>Status: {job.job_status}</li>
        <li>Face Name: {job.face_name}</li>
        <li>Image Key: {job.image_key}</li>
        <li>Video Key: {job.video_key}</li>
        <li>Created At: {new Date(job.created_at).toLocaleString()}</li>
      </ul>
    </div>
  );
}