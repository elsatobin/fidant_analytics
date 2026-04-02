import React, { useEffect, useState } from 'react';

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
  // State definitions (this was missing)
  const [days, setDays] = useState<DayStat[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem("access_token");

        if (!token) {
          setError("Please login first");
          setLoading(false);
          return;
        }

        const res = await fetch("http://localhost:5000/api/usage/stats", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (res.status === 401) {
          localStorage.removeItem("access_token");
          setError("Session expired. Please login again.");
          return;
        }

        const data = await res.json();

        // Update state
        setDays(data.days);
        setSummary(data.summary);

      } catch (err) {
        console.error(err);
        setError("Failed to fetch data");
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

      <h3>Daily Usage</h3>
      <ul>
        {days.map((day) => (
          <li key={day.date}>
            {day.date}: {day.committed}/{day.limit}
          </li>
        ))}
      </ul>

      {summary && (
        <>
          <h3>Summary</h3>
          <p>Total: {summary.total_committed}</p>
          <p>Average: {summary.avg_daily}</p>
          <p>Peak: {summary.peak_day.date} ({summary.peak_day.count})</p>
          <p>Streak: {summary.current_streak}</p>
        </>
      )}
    </div>
  );
};

export default UsageStats;