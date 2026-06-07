"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, BookOpen, Users, ArrowLeftRight } from "lucide-react";

const links = [
  { href: "/",        label: "Dashboard", icon: LayoutDashboard },
  { href: "/books",   label: "Books",     icon: BookOpen },
  { href: "/members", label: "Members",   icon: Users },
  { href: "/loans",   label: "Loans",     icon: ArrowLeftRight },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span>Neighborhood</span>
        <h1>Library</h1>
      </div>
      <nav className="sidebar-nav">
        {links.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={path === href ? "active" : ""}
          >
            <Icon size={16} />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
