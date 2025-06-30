"use client";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { AutomationRulesManager } from "@/components/settings/AutomationRulesManager";
import { VendorSettingsTable } from "@/components/shared/VendorSettingsTable";

export default function AiPoliciesPage() {
  return (
    <div className="space-y-6">
      <Tabs defaultValue="rules" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="rules">Automation Rules</TabsTrigger>
          <TabsTrigger value="vendors">Vendor Policies</TabsTrigger>
        </TabsList>
        <TabsContent value="rules">
          <Card>
            <CardHeader>
              <CardTitle>Automation Rules</CardTitle>
              <CardDescription>
                Create explicit rules to automatically process invoices. These rules are always followed and take precedence over learned patterns.
              </CardDescription>
            </CardHeader>
            <CardContent>
                <AutomationRulesManager />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="vendors">
            <VendorSettingsTable />
        </TabsContent>
      </Tabs>
    </div>
  );
} 