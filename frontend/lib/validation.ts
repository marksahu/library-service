/**
 * lib/validation.ts
 *
 * Client-side validation helpers.
 * All string fields are trimmed before validation and before submission.
 */

export type ValidationErrors = Record<string, string>;

/** Trim all string values in a form object. */
export function trimForm<T extends Record<string, unknown>>(form: T): T {
  return Object.fromEntries(
    Object.entries(form).map(([k, v]) => [k, typeof v === "string" ? v.trim() : v])
  ) as T;
}

/** Return true if a string is non-empty after trimming. */
export const isPresent = (v: unknown): boolean =>
  typeof v === "string" && v.trim().length > 0;

/** Simple email format check. */
export const isValidEmail = (v: string): boolean =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim());

// ─── Per-form validators ──────────────────────────────────────────────────────

export function validateBook(form: {
  title: string; author: string; copies: number; year?: number | string;
}): ValidationErrors {
  const errors: ValidationErrors = {};
  if (!isPresent(form.title))  errors.title  = "Title is required.";
  if (!isPresent(form.author)) errors.author = "Author is required.";
  if (!form.copies || Number(form.copies) < 1)
    errors.copies = "At least 1 copy is required.";
  if (form.year) {
    const y = Number(form.year);
    if (isNaN(y) || y < 1000 || y > 2100)
      errors.year = "Enter a valid year (1000–2100).";
  }
  return errors;
}

export function validateMember(form: {
  name: string; email: string;
}): ValidationErrors {
  const errors: ValidationErrors = {};
  if (!isPresent(form.name))  errors.name  = "Name is required.";
  if (!isPresent(form.email)) errors.email = "Email is required.";
  else if (!isValidEmail(form.email)) errors.email = "Enter a valid email address.";
  return errors;
}