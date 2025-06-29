"use client"; // This component now uses a hook, so it must be a client component

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard, FileUp, GanttChartSquare, Bot, Route, Cog } from "lucide-react";

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/document-hub", icon: FileUp, label: "Document Hub" },
  { href: "/ap-workbench", icon: GanttChartSquare, label: "AP Workbench" },
  { href: "/super-agent", icon: Bot, label: "Super Agent" },
  { href: "/invoice-explorer", icon: Route, label: "Invoice Explorer" },
  { href: "/ai-policy", icon: Cog, label: "AI Policy" },
];

export const Sidebar = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-blue-primary text-white p-4 flex flex-col shrink-0">
      <div className="text-2xl font-bold mb-10 text-center">Supervity</div>
      <nav>
        <ul>
          {navItems.map((item) => (
            <li key={item.label} className="mb-2">
              <Link
                href={item.href}
                className={cn(
                  "flex items-center p-3 rounded-lg text-sm font-medium transition-transform duration-200 ease-in-out hover:bg-blue-light/20 hover:translate-x-1",
                  pathname.startsWith(item.href) ? "bg-white/10 text-white" : "text-gray-100"
                )}
              >
                <item.icon className="mr-3 h-5 w-5" />
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}; 