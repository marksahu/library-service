"use client";
import { useEffect, useState, useCallback } from "react";
import { api, Loan, Book, Member } from "@/lib/api";
import { Plus, Search, RotateCcw, X, ArrowLeftRight, AlertTriangle } from "lucide-react";

export default function LoansPage() {
  const [loans, setLoans]       = useState<Loan[]>([]);
  const [total, setTotal]       = useState(0);
  const [activeOnly, setActive] = useState(false);
  const [page, setPage]         = useState(1);
  const [modal, setModal]       = useState(false);

  // borrow form
  const [books, setBooks]       = useState<Book[]>([]);
  const [members, setMembers]   = useState<Member[]>([]);
  const [memberId, setMemberId] = useState("");
  const [bookId, setBookId]     = useState("");
  const [loanDays, setLoanDays] = useState(14);

  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [success, setSuccess]   = useState("");

  const load = useCallback(() => {
    api.loans.list({ active_only: activeOnly, page }).then(r => { setLoans(r.loans); setTotal(r.total); });
  }, [activeOnly, page]);

  useEffect(() => { load(); }, [load]);

  const openBorrow = async () => {
    setError("");
    const [b, m] = await Promise.all([
      api.books.list("", 1).then(r => r.books.filter(bk => bk.available > 0)),
      api.members.list("", 1).then(r => r.members.filter(m => m.active)),
    ]);
    setBooks(b); setMembers(m);
    setMemberId(""); setBookId(""); setLoanDays(14);
    setModal(true);
  };

  const borrow = async () => {
    if (!memberId || !bookId) { setError("Please select both a member and a book."); return; }
    setLoading(true); setError("");
    try {
      await api.loans.borrow(Number(memberId), Number(bookId), loanDays);
      setSuccess("Book borrowed successfully.");
      setModal(false); load();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const returnBook = async (loan: Loan) => {
    if (!confirm(`Return "${loan.book_title}" for ${loan.member_name}?`)) return;
    try {
      await api.loans.returnBook(loan.id);
      setSuccess("Book returned.");
      load();
    } catch (e: any) { setError(e.message); }
  };

  return (
    <>
      <div className="page-header">
        <h2>Loans</h2>
        <p>Track borrowing and returns</p>
      </div>
      <div className="page-body">
        {success && <div className="alert alert-success">{success}</div>}
        {error && !modal && <div className="alert alert-error">{error}</div>}

        <div className="toolbar">
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.875rem", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={e => { setActive(e.target.checked); setPage(1); }}
              style={{ width: "auto" }}
            />
            Active loans only
          </label>
          <button className="btn btn-primary" onClick={openBorrow}>
            <Plus size={15} /> Borrow Book
          </button>
        </div>

        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Member</th><th>Book</th><th>Borrowed</th>
                  <th>Due</th><th>Returned</th><th>Fine</th><th>Status</th><th></th>
                </tr>
              </thead>
              <tbody>
                {loans.length === 0 && (
                  <tr><td colSpan={8}>
                    <div className="empty-state">
                      <ArrowLeftRight size={40} />
                      <h4>No loans found</h4>
                    </div>
                  </td></tr>
                )}
                {loans.map(l => (
                  <tr key={l.id}>
                    <td><strong>{l.member_name}</strong></td>
                    <td>{l.book_title}</td>
                    <td className="td-muted">{new Date(l.borrowed_at).toLocaleDateString()}</td>
                    <td className="td-muted">{new Date(l.due_at).toLocaleDateString()}</td>
                    <td className="td-muted">
                      {l.returned_at ? new Date(l.returned_at).toLocaleDateString() : "—"}
                    </td>
                    <td>
                      {l.fine_amount > 0
                        ? <span className="badge badge-red">${l.fine_amount.toFixed(2)}</span>
                        : <span className="td-muted">$0.00</span>
                      }
                    </td>
                    <td>
                      {l.returned_at ? (
                        <span className="badge badge-gray">Returned</span>
                      ) : l.overdue ? (
                        <span className="badge badge-red"><AlertTriangle size={10} /> Overdue</span>
                      ) : (
                        <span className="badge badge-blue">Active</span>
                      )}
                    </td>
                    <td>
                      {!l.returned_at && (
                        <button className="btn btn-success btn-sm" onClick={() => returnBook(l)}>
                          <RotateCcw size={12} /> Return
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {total > 20 && (
            <div style={{ padding: "12px 16px", display: "flex", gap: 8, justifyContent: "flex-end" }}>
              <button className="btn btn-outline btn-sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Prev</button>
              <span style={{ lineHeight: "30px", fontSize: "0.8rem", color: "var(--ink-light)" }}>
                {page} / {Math.ceil(total / 20)}
              </span>
              <button className="btn btn-outline btn-sm" disabled={page * 20 >= total} onClick={() => setPage(p => p + 1)}>Next</button>
            </div>
          )}
        </div>
      </div>

      {modal && (
        <div className="modal-backdrop" onClick={() => setModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Borrow a Book</h3>
              <button className="btn btn-ghost" onClick={() => setModal(false)}><X size={16} /></button>
            </div>
            <div className="modal-body">
              {error && <div className="alert alert-error">{error}</div>}
              <div className="form-group">
                <label>Member *</label>
                <select value={memberId} onChange={e => setMemberId(e.target.value)}>
                  <option value="">— Select member —</option>
                  {members.map(m => (
                    <option key={m.id} value={m.id}>{m.name} ({m.email})</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Book *</label>
                <select value={bookId} onChange={e => setBookId(e.target.value)}>
                  <option value="">— Select available book —</option>
                  {books.map(b => (
                    <option key={b.id} value={b.id}>
                      {b.title} – {b.author} ({b.available} available)
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Loan Period (days)</label>
                <input
                  type="number" min={1} max={180} value={loanDays}
                  onChange={e => setLoanDays(Number(e.target.value))}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-outline" onClick={() => setModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={borrow} disabled={loading}>
                {loading ? "Processing…" : "Confirm Borrow"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
