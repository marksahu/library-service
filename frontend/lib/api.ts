import { API_BASE, ENDPOINTS, PAGE_SIZE } from "./constants";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface Book {
  id: number; title: string; author: string; isbn?: string;
  genre?: string; year?: number; copies: number; available: number;
}
export interface Member {
  id: number; name: string; email: string; phone?: string;
  address?: string; active: boolean; joined_at: string;
}
export interface Loan {
  id: number; member_id: number; book_id: number;
  member_name: string; book_title: string;
  borrowed_at: string; due_at: string; returned_at?: string;
  overdue: boolean; fine_amount: number;
}
export interface DashboardStats {
  total_books: number; total_members: number;
  active_loans: number; overdue_loans: number; total_fines: number;
}

// ─── API client ───────────────────────────────────────────────────────────────

export const api = {
  books: {
    list: (search = "", page = 1) =>
      request<{ books: Book[]; total: number }>(
        `${ENDPOINTS.books}?search=${encodeURIComponent(search)}&page=${page}&limit=${PAGE_SIZE}`
      ),
    get:    (id: number) => request<Book>(ENDPOINTS.book(id)),
    create: (data: Omit<Book, "id" | "available">) =>
      request<Book>(ENDPOINTS.books, { method: "POST", body: JSON.stringify(data) }),
    update: (id: number, data: Partial<Book>) =>
      request<Book>(ENDPOINTS.book(id), { method: "PATCH", body: JSON.stringify(data) }),
    delete: (id: number) => request<void>(ENDPOINTS.book(id), { method: "DELETE" }),
  },

  members: {
    list: (search = "", page = 1) =>
      request<{ members: Member[]; total: number }>(
        `${ENDPOINTS.members}?search=${encodeURIComponent(search)}&page=${page}&limit=${PAGE_SIZE}`
      ),
    get:    (id: number) => request<Member>(ENDPOINTS.member(id)),
    create: (data: Omit<Member, "id" | "active" | "joined_at">) =>
      request<Member>(ENDPOINTS.members, { method: "POST", body: JSON.stringify(data) }),
    update: (id: number, data: Partial<Member>) =>
      request<Member>(ENDPOINTS.member(id), { method: "PATCH", body: JSON.stringify(data) }),
    delete: (id: number) => request<void>(ENDPOINTS.member(id), { method: "DELETE" }),
  },

  loans: {
    list: (params: { member_id?: number; book_id?: number; active_only?: boolean; page?: number }) => {
      const q = new URLSearchParams();
      if (params.member_id)   q.set("member_id",   String(params.member_id));
      if (params.book_id)     q.set("book_id",      String(params.book_id));
      if (params.active_only) q.set("active_only",  "true");
      q.set("page",  String(params.page ?? 1));
      q.set("limit", String(PAGE_SIZE));
      return request<{ loans: Loan[]; total: number }>(`${ENDPOINTS.loans}?${q}`);
    },
    borrow: (member_id: number, book_id: number, loan_days = 14) =>
      request<Loan>(ENDPOINTS.borrow, {
        method: "POST",
        body: JSON.stringify({ member_id, book_id, loan_days }),
      }),
    returnBook: (loan_id: number) =>
      request<Loan>(ENDPOINTS.returnLoan(loan_id), { method: "POST" }),
  },

  dashboard: () => request<DashboardStats>(ENDPOINTS.dashboard),
};