"use client";
/**
 * components/ErrorBoundary.tsx
 *
 * Application-level error boundary. Catches unhandled render errors and
 * shows a fallback UI instead of a blank screen.
 */
import { Component, ReactNode } from "react";

interface Props   { children: ReactNode; }
interface State   { hasError: boolean; message: string; }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: "" };

  static getDerivedStateFromError(err: Error): State {
    return { hasError: true, message: err.message };
  }

  componentDidCatch(err: Error, info: React.ErrorInfo) {
    console.error("[ErrorBoundary]", err, info.componentStack);
  }

  handleReset = () => this.setState({ hasError: false, message: "" });

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center",
          justifyContent: "center", minHeight: "60vh", gap: 16, padding: 32,
        }}>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.5rem" }}>
            Something went wrong
          </h2>
          <p style={{ color: "var(--ink-light)", fontSize: "0.875rem", maxWidth: 400, textAlign: "center" }}>
            {this.state.message || "An unexpected error occurred."}
          </p>
          <button className="btn btn-primary" onClick={this.handleReset}>
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}