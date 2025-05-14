import React from 'react';
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div>
      <h1>Welcome</h1>
      <p>
        <Link to="/login">Login</Link> or <Link to="/upload">Start Upload</Link>
      </p>
    </div>
  );
}