import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { AutomationRulesTable } from "@/components/shared/AutomationRulesTable";
import { LearnedHeuristicsTable } from "@/components/shared/LearnedHeuristicsTable";
import { VendorSettingsTable } from "@/components/shared/VendorSettingsTable";

export default function AiPolicyPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-black">AI Policy & Learnings</h1>
      <Tabs defaultValue="rules" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="rules">Automation Rules</TabsTrigger>
          <TabsTrigger value="heuristics">Learned Heuristics</TabsTrigger>
          <TabsTrigger value="vendors">Vendor Settings</TabsTrigger>
        </TabsList>
        <TabsContent value="rules">
          <Card>
            <CardHeader>
              <CardTitle>Automation Rules</CardTitle>
              <CardDescription>
                Explicit rules to automatically process invoices. These are always followed.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AutomationRulesTable />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="heuristics">
          <Card>
            <CardHeader>
              <CardTitle>Learned Heuristics</CardTitle>
              <CardDescription>
                Patterns the AI has learned from your actions. High-confidence heuristics can be promoted to rules.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LearnedHeuristicsTable />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="vendors">
          <Card>
            <CardHeader>
              <CardTitle>Vendor Settings</CardTitle>
              <CardDescription>
                Manage vendor-specific configurations like price tolerance.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <VendorSettingsTable />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 