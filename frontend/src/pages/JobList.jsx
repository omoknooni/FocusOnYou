import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

export default function JobsList() {
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    api.get('/jobs').then(res => setJobs(res.data));
  }, []);

  return (
    <div>
      <h2>My Jobs</h2>
      <table>
        <thead>
          <tr>
            <th>Job ID</th>
            <th>Status</th>
            <th>Created At</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map(job => (
            <tr key={job.job_id}>
              <td><Link to={`/jobs/${job.job_id}`}>{job.job_id}</Link></td>
              <td>{job.job_status}</td>
              <td>{new Date(job.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}