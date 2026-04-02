import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface DayStat {
  date: string;
  committed: number;
  reserved: number;
  limit: number;
}

interface Summary {
  total_committed: number;
  avg_daily: number;
  peak_day: { date: string; count: number };
  current_streak: number;
}

const UsageStats: React.FC = () => {
  const [days, setDays] = useState<DayStat[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Get token saved after login
        const token = localStorage.getItem('access_token'); 
        if (!token) {
          setError('No access token found. Please login first.');
          setLoading(false);
          return;
        }

        // Request data from FastAPI server (port 5000)
        const res = await axios.get('http://localhost:5000/api/usage/stats?days=7', {
          headers: {
            Authorization: `Bearer ${token}`, // Send JWT token
          },
        });

        setDays(res.data.days);
        setSummary(res.data.summary);
      } catch (err) {
        console.error(err);
        setError('Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error}</p>;

  return (
    <div>
      <h2>Usage Stats</h2>
      <div>
        <h3>Daily Usage</h3>
        <ul>
          {days.map((day) => (
            <li key={day.date}>
              {day.date}: {day.committed}/{day.limit} used
            </li>
          ))}
        </ul>
      </div>
      {summary && (
        <div>
          <h3>Summary</h3>
          <p>Total Committed: {summary.total_committed}</p>
          <p>Average Daily: {summary.avg_daily}</p>
          <p>Peak Day: {summary.peak_day.date} ({summary.peak_day.count})</p>
          <p>Current Streak: {summary.current_streak}</p>
        </div>
      )}
    </div>
  );
};

export default UsageStats;