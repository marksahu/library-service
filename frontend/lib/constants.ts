/**
 * lib/constants.ts
 *
 * Single source of truth for all API endpoint paths.
 * Pages and lib/api.ts import from here — no hardcoded strings elsewhere.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const ENDPOINTS = {
  // Books
  books:      "/books",
  book:       (id: number) => `/books/${id}`,

  // Members
  members:    "/members",
  member:     (id: number) => `/members/${id}`,

  // Loans
  loans:      "/loans",
  loan:       (id: number) => `/loans/${id}`,
  borrow:     "/loans/borrow",
  returnLoan: (id: number) => `/loans/${id}/return`,

  // Other
  dashboard:  "/dashboard",
  health:     "/health",
} as const;

export const PAGE_SIZE = 20;