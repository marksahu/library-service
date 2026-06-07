"use client";
import { useEffect, useState, useCallback } from "react";
import { api, Book } from "@/lib/api";
import { Plus, Search, Pencil, Trash2, X, BookOpen } from "lucide-react";

const empty: Omit<Book, "id" | "available"> = {
  title: "", author: "", isbn: "", genre: "", year: undefined as any, copies: 1,
};

export default function BooksPage() {
  const [books, setBooks]       = useState<Book[]>([]);
  const [total, setTotal]       = useState(0);
  const [search, setSearch]     = useState("");
  const [page, setPage]         = useState(1);
  const [modal, setModal]       = useState<"create" | "edit" | null>(null);
  const [form, setForm]         = useState({ ...empty });
  const [editing, setEditing]   = useState<Book | null>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [success, setSuccess]   = useState("");

  const load = useCallback(() => {
    api.books.list(search, page).then(r => { setBooks(r.books); setTotal(r.total); });
  }, [search, page]);

  useEffect(() => { load(); }, [load]);

  const openCreate = () => { setForm({ ...empty }); setEditing(null); setError(""); setModal("create"); };
  const openEdit   = (b: Book) => {
    setForm({ title: b.title, author: b.author, isbn: b.isbn || "", genre: b.genre || "", year: b.year as any, copies: b.copies });
    setEditing(b); setError(""); setModal("edit");
  };

  const submit = async () => {
    setLoading(true); setError("");
    try {
      if (modal === "create") {
        await api.books.create({ ...form, copies: Number(form.copies), year: form.year ? Number(form.year) : undefined });
        setSuccess("Book added successfully.");
      } else if (editing) {
        await api.books.update(editing.id, { ...form, copies: Number(form.copies), year: form.year ? Number(form.year) : undefined });
        setSuccess("Book updated.");
      }
      setModal(null); load();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const del = async (id: number) => {
    if (!confirm("Delete this book?")) return;
    try { await api.books.delete(id); setSuccess("Book deleted."); load(); }
    catch (e: any) { setError(e.message); }
  };

  return (
    <>
      <div className="page-header">
        <h2>Books</h2>
        <p>Manage the library catalogue</p>
      </div>
      <div className="page-body">
        {success && <div className="alert alert-success">{success}</div>}
        {error && !modal && <div className="alert alert-error">{error}</div>}

        <div className="toolbar">
          <div className="search-wrap">
            <Search size={15} />
            <input
              placeholder="Search by title or author…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
            />
          </div>
          <button className="btn btn-primary" onClick={openCreate}>
            <Plus size={15} /> Add Book
          </button>
        </div>

        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Title</th><th>Author</th><th>ISBN</th>
                  <th>Genre</th><th>Year</th><th>Copies</th><th>Available</th><th></th>
                </tr>
              </thead>
              <tbody>
                {books.length === 0 && (
                  <tr><td colSpan={8}>
                    <div className="empty-state">
                      <BookOpen size={40} />
                      <h4>No books yet</h4>
                      <p>Add the first book to the catalogue.</p>
                    </div>
                  </td></tr>
                )}
                {books.map(b => (
                  <tr key={b.id}>
                    <td><strong>{b.title}</strong></td>
                    <td className="td-muted">{b.author}</td>
                    <td className="td-mono">{b.isbn || "—"}</td>
                    <td className="td-muted">{b.genre || "—"}</td>
                    <td className="td-muted">{b.year || "—"}</td>
                    <td>{b.copies}</td>
                    <td>
                      <span className={`badge ${b.available > 0 ? "badge-green" : "badge-red"}`}>
                        {b.available} / {b.copies}
                      </span>
                    </td>
                    <td style={{ display: "flex", gap: 4 }}>
                      <button className="btn btn-ghost btn-sm" onClick={() => openEdit(b)}>
                        <Pencil size={13} />
                      </button>
                      <button className="btn btn-ghost btn-sm" onClick={() => del(b.id)}>
                        <Trash2 size={13} />
                      </button>
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
                Page {page} of {Math.ceil(total / 20)}
              </span>
              <button className="btn btn-outline btn-sm" disabled={page * 20 >= total} onClick={() => setPage(p => p + 1)}>Next</button>
            </div>
          )}
        </div>
      </div>

      {modal && (
        <div className="modal-backdrop" onClick={() => setModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{modal === "create" ? "Add New Book" : "Edit Book"}</h3>
              <button className="btn btn-ghost" onClick={() => setModal(null)}><X size={16} /></button>
            </div>
            <div className="modal-body">
              {error && <div className="alert alert-error">{error}</div>}
              <div className="form-row">
                <div className="form-group">
                  <label>Title *</label>
                  <input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label>Author *</label>
                  <input value={form.author} onChange={e => setForm(f => ({ ...f, author: e.target.value }))} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>ISBN</label>
                  <input value={form.isbn} onChange={e => setForm(f => ({ ...f, isbn: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label>Genre</label>
                  <input value={form.genre} onChange={e => setForm(f => ({ ...f, genre: e.target.value }))} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Publication Year</label>
                  <input type="number" value={form.year ?? ""} onChange={e => setForm(f => ({ ...f, year: e.target.value as any }))} />
                </div>
                <div className="form-group">
                  <label>Number of Copies</label>
                  <input type="number" min={1} value={form.copies} onChange={e => setForm(f => ({ ...f, copies: Number(e.target.value) }))} />
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-outline" onClick={() => setModal(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={submit} disabled={loading}>
                {loading ? "Saving…" : modal === "create" ? "Add Book" : "Save Changes"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
