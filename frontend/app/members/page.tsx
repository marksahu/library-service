"use client";
import { useEffect, useState, useCallback } from "react";
import { api, Member } from "@/lib/api";
import { Plus, Search, Pencil, UserX, X, Users } from "lucide-react";

const empty = { name: "", email: "", phone: "", address: "" };

export default function MembersPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [total, setTotal]     = useState(0);
  const [search, setSearch]   = useState("");
  const [page, setPage]       = useState(1);
  const [modal, setModal]     = useState<"create" | "edit" | null>(null);
  const [form, setForm]       = useState({ ...empty });
  const [editing, setEditing] = useState<Member | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");
  const [success, setSuccess] = useState("");

  const load = useCallback(() => {
    api.members.list(search, page).then(r => { setMembers(r.members); setTotal(r.total); });
  }, [search, page]);

  useEffect(() => { load(); }, [load]);

  const openCreate = () => { setForm({ ...empty }); setEditing(null); setError(""); setModal("create"); };
  const openEdit   = (m: Member) => {
    setForm({ name: m.name, email: m.email, phone: m.phone || "", address: m.address || "" });
    setEditing(m); setError(""); setModal("edit");
  };

  const submit = async () => {
    setLoading(true); setError("");
    try {
      if (modal === "create") await api.members.create(form);
      else if (editing)       await api.members.update(editing.id, form);
      setSuccess(modal === "create" ? "Member registered." : "Member updated.");
      setModal(null); load();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const deactivate = async (m: Member) => {
    if (!confirm(`Deactivate ${m.name}?`)) return;
    try { await api.members.delete(m.id); setSuccess("Member deactivated."); load(); }
    catch (e: any) { setError(e.message); }
  };

  return (
    <>
      <div className="page-header">
        <h2>Members</h2>
        <p>Registered library patrons</p>
      </div>
      <div className="page-body">
        {success && <div className="alert alert-success">{success}</div>}
        {error && !modal && <div className="alert alert-error">{error}</div>}

        <div className="toolbar">
          <div className="search-wrap">
            <Search size={15} />
            <input
              placeholder="Search by name or email…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
            />
          </div>
          <button className="btn btn-primary" onClick={openCreate}>
            <Plus size={15} /> Add Member
          </button>
        </div>

        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th><th>Email</th><th>Phone</th>
                  <th>Joined</th><th>Status</th><th></th>
                </tr>
              </thead>
              <tbody>
                {members.length === 0 && (
                  <tr><td colSpan={6}>
                    <div className="empty-state">
                      <Users size={40} />
                      <h4>No members yet</h4>
                      <p>Register the first patron.</p>
                    </div>
                  </td></tr>
                )}
                {members.map(m => (
                  <tr key={m.id}>
                    <td><strong>{m.name}</strong></td>
                    <td className="td-muted">{m.email}</td>
                    <td className="td-muted">{m.phone || "—"}</td>
                    <td className="td-muted">{new Date(m.joined_at).toLocaleDateString()}</td>
                    <td>
                      <span className={`badge ${m.active ? "badge-green" : "badge-gray"}`}>
                        {m.active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td style={{ display: "flex", gap: 4 }}>
                      <button className="btn btn-ghost btn-sm" onClick={() => openEdit(m)}>
                        <Pencil size={13} />
                      </button>
                      {m.active && (
                        <button className="btn btn-ghost btn-sm" title="Deactivate" onClick={() => deactivate(m)}>
                          <UserX size={13} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {modal && (
        <div className="modal-backdrop" onClick={() => setModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{modal === "create" ? "Register Member" : "Edit Member"}</h3>
              <button className="btn btn-ghost" onClick={() => setModal(null)}><X size={16} /></button>
            </div>
            <div className="modal-body">
              {error && <div className="alert alert-error">{error}</div>}
              <div className="form-row">
                <div className="form-group">
                  <label>Full Name *</label>
                  <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label>Email *</label>
                  <input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Phone</label>
                  <input value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label>Address</label>
                  <input value={form.address} onChange={e => setForm(f => ({ ...f, address: e.target.value }))} />
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-outline" onClick={() => setModal(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={submit} disabled={loading}>
                {loading ? "Saving…" : modal === "create" ? "Register" : "Save Changes"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
