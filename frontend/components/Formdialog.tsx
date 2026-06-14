"use client";
/**
 * components/FormDialog.tsx
 *
 * Reusable modal shell for Create / Edit forms.
 * Handles: backdrop click to close, header, scrollable body, footer with
 * Cancel + Submit buttons, error alert, and disabled state during loading.
 */
import { X } from "lucide-react";

interface Props {
  open:          boolean;
  title:         string;
  submitLabel:   string;
  loading:       boolean;
  error:         string;
  onSubmit:      () => void;
  onClose:       () => void;
  children:      React.ReactNode;
}

export default function FormDialog({
  open, title, submitLabel, loading, error, onSubmit, onClose, children,
}: Props) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="btn btn-ghost" onClick={onClose} disabled={loading}>
            <X size={16} />
          </button>
        </div>
        <div className="modal-body">
          {error && <div className="alert alert-error">{error}</div>}
          {children}
        </div>
        <div className="modal-footer">
          <button className="btn btn-outline" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={onSubmit} disabled={loading}>
            {loading ? "Saving…" : submitLabel}
          </button>
        </div>
      </div>
    </div>
  );
}