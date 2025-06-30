import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { AutomationRulesTable } from "@/components/shared/AutomationRulesTable";
import { VendorSettingsTable } from "@/components/shared/VendorSettingsTable";

// Placeholder for General Settings UI
const GeneralSettings = () => (
    <Card>
        <CardHeader>
            <CardTitle>General Settings</CardTitle>
            <CardDescription>
                Define system-wide policies and default behaviors.
            </CardDescription>
        </CardHeader>
        <CardContent>
            <div className="space-y-6">
                <div>
                    <h4 className="font-semibold">Default Tolerances</h4>
                    <p className="text-sm text-gray-500 mb-2">Applied to vendors without specific settings.</p>
                    {/* UI for these settings would go here */}
                </div>
                <div>
                    <h4 className="font-semibold">Duplicate Invoice Policy</h4>
                     <p className="text-sm text-gray-500 mb-2">How to handle invoices that appear to be duplicates.</p>
                </div>
            </div>
        </CardContent>
    </Card>
);

export default function ConfigurationPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Configuration Hub</h1>
      <Tabs defaultValue="vendors" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="vendors">Vendor Configuration</TabsTrigger>
          <TabsTrigger value="rules">Automation Rules</TabsTrigger>
          <TabsTrigger value="general">General Policies</TabsTrigger>
        </TabsList>
        <TabsContent value="vendors">
            <VendorSettingsTable />
        </TabsContent>
        <TabsContent value="rules">
          <Card>
            <CardHeader>
              <CardTitle>Automation Rules</CardTitle>
              <CardDescription>Explicit rules to automatically process invoices. These are always followed.</CardDescription>
            </CardHeader>
            <CardContent><AutomationRulesTable /></CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="general">
            <GeneralSettings />
        </TabsContent>
      </Tabs>
    </div>
  );
} 