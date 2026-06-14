"use client";
/**
 * components/DataTable.tsx
 *
 * Reusable table component used by Books, Members, and Loans pages.
 * Handles:
 *  - Loading skeleton rows
 *  - Inline error state for failed list requests
 *  - Empty state with custom icon + message
 *  - Server-side pagination
 */
import { PAGE_SIZE } from "@/lib/constants";

interface Column<T> {
  header: string;
  render: (row: T) => React.ReactNode;
  width?: string;
}

interface Props<T> {
  columns:    Column<T>[];
  rows:       T[];
  keyFn:      (row: T) => string | number;
  loading:    boolean;
  error:      string;
  total:      number;
  page:       number;
  onPage:     (p: number) => void;
  emptyIcon:  React.ReactNode;
  emptyText:  string;
}

function SkeletonRow({ cols }: { cols: number }) {
  return (
    <tr>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i}>
          <div className="skeleton" style={{ height: 14, width: i === 0 ? "60%" : "80%", borderRadius: 4 }} />
        </td>
      ))}
    </tr>
  );
}

export default function DataTable<T>({
  columns, rows, keyFn, loading, error, total, page, onPage, emptyIcon, emptyText,
}: Props<T>) {
  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="card">
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map(c => (
                <th key={c.header} style={c.width ? { width: c.width } : {}}>
                  {c.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Loading state */}
            {loading && rows.length === 0 && (
              Array.from({ length: 5 }).map((_, i) => (
                <SkeletonRow key={i} cols={columns.length} />
              ))
            )}

            {/* Error state */}
            {!loading && error && (
              <tr>
                <td colSpan={columns.length}>
                  <div className="empty-state">
                    <p style={{ color: "var(--danger)", fontSize: "0.875rem" }}>
                      ⚠ {error}
                    </p>
                  </div>
                </td>
              </tr>
            )}

            {/* Empty state */}
            {!loading && !error && rows.length === 0 && (
              <tr>
                <td colSpan={columns.length}>
                  <div className="empty-state">
                    {emptyIcon}
                    <h4>{emptyText}</h4>
                  </div>
                </td>
              </tr>
            )}

            {/* Data rows */}
            {!error && rows.map(row => (
              <tr key={keyFn(row)}>
                {columns.map(c => (
                  <td key={c.header}>{c.render(row)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="btn btn-outline btn-sm"
            disabled={page === 1 || loading}
            onClick={() => onPage(page - 1)}
          >
            Prev
          </button>
          <span className="pagination-label">
            Page {page} of {totalPages}
          </span>
          <button
            className="btn btn-outline btn-sm"
            disabled={page >= totalPages || loading}
            onClick={() => onPage(page + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}