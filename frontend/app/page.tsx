"use client";
import { useEffect, useState } from "react";
import { api, DashboardStats, Loan } from "@/lib/api";
import { BookOpen, Users, ArrowLeftRight, AlertTriangle, DollarSign } from "lucide-react";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [overdue, setOverdue] = useState<Loan[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.dashboard().then(setStats).catch(e => setError(e.message));
    api.loans.list({ active_only: true, page: 1 }).then(r => {
      setOverdue(r.loans.filter(l => l.overdue).slice(0, 5));
    });
  }, []);

  return (
    <>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Library at a glance</p>
      </div>
      <div className="page-body">
        {error && <div className="alert alert-error">{error}</div>}

        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-label">Total Books</div>
            <div className="stat-value">{stats?.total_books ?? "—"}</div>
            <div className="stat-sub">titles in catalogue</div>
          </div>
          <div className="stat-card success">
            <div className="stat-label">Active Members</div>
            <div className="stat-value">{stats?.total_members ?? "—"}</div>
            <div className="stat-sub">registered &amp; active</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Active Loans</div>
            <div className="stat-value">{stats?.active_loans ?? "—"}</div>
            <div className="stat-sub">books currently out</div>
          </div>
          <div className="stat-card danger">
            <div className="stat-label">Overdue</div>
            <div className="stat-value">{stats?.overdue_loans ?? "—"}</div>
            <div className="stat-sub">past due date</div>
          </div>
          <div className="stat-card warning">
            <div className="stat-label">Total Fines</div>
            <div className="stat-value">
              ${stats ? stats.total_fines.toFixed(2) : "—"}
            </div>
            <div className="stat-sub">accumulated</div>
          </div>
        </div>

        {overdue.length > 0 && (
          <div className="card">
            <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
              <AlertTriangle size={16} color="var(--warning)" />
              <strong style={{ fontSize: "0.875rem" }}>Overdue Returns</strong>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Member</th>
                    <th>Book</th>
                    <th>Due Date</th>
                    <th>Fine</th>
                  </tr>
                </thead>
                <tbody>
                  {overdue.map(l => (
                    <tr key={l.id}>
                      <td>{l.member_name}</td>
                      <td>{l.book_title}</td>
                      <td className="td-muted">{new Date(l.due_at).toLocaleDateString()}</td>
                      <td>
                        <span className="badge badge-red">${l.fine_amount.toFixed(2)}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
