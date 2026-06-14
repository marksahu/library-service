"use client";
/**
 * components/ConfirmDialog.tsx
 *
 * Custom confirm dialog — replaces all window.confirm() calls.
 * Usage:
 *   <ConfirmDialog
 *     open={!!pending}
 *     title="Deactivate Member"
 *     message={`Deactivate ${pending?.name}?`}
 *     confirmLabel="Deactivate"
 *     danger
 *     onConfirm={handleConfirm}
 *     onCancel={() => setPending(null)}
 *   />
 */
import { X } from "lucide-react";

interface Props {
  open:         boolean;
  title:        string;
  message:      string;
  confirmLabel?: string;
  danger?:      boolean;
  loading?:     boolean;
  onConfirm:    () => void;
  onCancel:     () => void;
}

export default function ConfirmDialog({
  open, title, message, confirmLabel = "Confirm",
  danger = false, loading = false, onConfirm, onCancel,
}: Props) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div className="modal" style={{ maxWidth: 400 }} onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="btn btn-ghost" onClick={onCancel} disabled={loading}>
            <X size={16} />
          </button>
        </div>
        <div className="modal-body">
          <p style={{ fontSize: "0.9rem", color: "var(--ink-mid)" }}>{message}</p>
        </div>
        <div className="modal-footer">
          <button className="btn btn-outline" onClick={onCancel} disabled={loading}>
            Cancel
          </button>
          <button
            className={`btn ${danger ? "btn-accent" : "btn-primary"}`}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? "Please wait…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}