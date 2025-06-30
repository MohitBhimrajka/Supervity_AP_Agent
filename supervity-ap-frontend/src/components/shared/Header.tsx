"use client"; // This component also needs the pathname hook

import { usePathname } from "next/navigation";
import { Bot } from "lucide-react";
import { useAppContext } from "@/lib/AppContext";
import { Button } from "../ui/Button";

// This helper gets the title from the path for the header
const getPageTitle = (path: string) => {
    // Match the path to the labels in Sidebar.tsx
    const navMap: Record<string, string> = {
        "/dashboard": "Dashboard",
        "/data-center": "Data Center",
        "/invoice-explorer": "Invoice Explorer",
        "/resolution-workbench": "Resolution Workbench",
        "/learned-insights": "Learned Insights",
        "/payment-center": "Payment Center",
        "/settings": "Settings",
    };

    // Find a matching key that the path starts with
    const matchingKey = Object.keys(navMap).find(key => path.startsWith(key));
    if (matchingKey) {
        return navMap[matchingKey];
    }
    
    // Fallback for unmapped pages
    const title = path.replace('/', '').replace('-', ' ');
    return title.charAt(0).toUpperCase() + title.slice(1);
};

export const Header = () => {
  const pathname = usePathname();
  const { openCanvas } = useAppContext();
  const title = getPageTitle(pathname);

  const handleCopilotClick = () => {
    openCanvas({
      title: "AP Copilot",
      type: 'copilot'
    });
  };

  return (
    <header className="bg-white border-b border-gray-light p-4 flex justify-between items-center shrink-0">
      <h1 className="text-xl font-semibold text-gray-dark">{title}</h1>
      <div className="flex items-center">
        <Button 
          variant="primary"
          onClick={handleCopilotClick} 
        >
          <Bot className="mr-2 h-5 w-5" />
          <span>Ask Copilot</span>
        </Button>
      </div>
    </header>
  );
}; 