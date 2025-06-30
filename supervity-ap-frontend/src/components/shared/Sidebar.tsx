"use client"; // This component now uses a hook, so it must be a client component

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { 
  LayoutDashboard, 
  GanttChartSquare, 
  DatabaseZap, // New Icon for Data Center
  ClipboardList, // New Icon for Invoice Manager
  SlidersHorizontal, // New Icon for Configuration
  Sparkles // New Icon for Automation
} from "lucide-react";

// New navigation structure (Copilot removed)
const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/data-center", icon: DatabaseZap, label: "Data Center" },
  { href: "/invoice-explorer", icon: GanttChartSquare, label: "Invoice Explorer" },
  { href: "/resolution-workbench", icon: ClipboardList, label: "Resolution Workbench" },
  { href: "/ai-insights", icon: Sparkles, label: "AI Insights" },
  { href: "/ai-policies", icon: SlidersHorizontal, label: "AI Policies" },
];

export const Sidebar = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-blue-primary text-white p-4 flex flex-col shrink-0">
      <div className="mb-10 px-4">
        <Link href="/dashboard">
            <Image
                src="/logo.svg"
                alt="Supervity Logo"
                width={150}
                height={40}
                priority
            />
        </Link>
      </div>
      <nav>
        <ul>
          {navItems.map((item) => (
            <li key={item.label} className="mb-2">
              <Link
                href={item.href}
                className={cn(
                  "flex items-center p-3 rounded-lg text-sm font-medium transition-transform duration-200 ease-in-out hover:bg-white/20 hover:translate-x-1",
                  pathname === item.href || (pathname.startsWith(item.href) && item.href !== '/')
                    ? "bg-white/10 text-white font-semibold" 
                    : "text-gray-200 hover:text-white"
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