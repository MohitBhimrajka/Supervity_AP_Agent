"use client"; // This component also needs the pathname hook

import { usePathname } from "next/navigation";
import { Bell } from "lucide-react";

// A simple helper to get the title from the path
const getPageTitle = (path: string) => {
  switch (path) {
    case "/dashboard":
      return "Dashboard";
    case "/document-hub":
      return "Document Hub";
    case "/ap-workbench":
      return "AP Workbench";
    // Add other cases as we build them
    default:
      // A better default for pages we haven't mapped yet
      const title = path.replace('/', '').replace('-', ' ');
      return title.charAt(0).toUpperCase() + title.slice(1);
  }
};


export const Header = () => {
  const pathname = usePathname();
  const title = getPageTitle(pathname);

  return (
    <header className="bg-white border-b border-gray-light p-4 flex justify-between items-center shrink-0">
      <h1 className="text-xl font-semibold text-black">{title}</h1>
      <div>
        <button className="relative">
          <Bell className="h-6 w-6 text-gray-dark" />
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-pink-destructive opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-pink-destructive"></span>
          </span>
        </button>
      </div>
    </header>
  );
}; 