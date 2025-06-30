"use client";
import { useEffect, useState, FormEvent } from "react";
import { getLearnedHeuristics, createAutomationRule, type AggregatedHeuristic, type AutomationRuleCreate } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import toast from "react-hot-toast";
import { ArrowRight, Sparkles } from "lucide-react";

const ConfidenceBar = ({ score }: { score: number }) => (
    <div className="w-full bg-gray-200 rounded-full h-2.5">
      <div className="bg-purple-accent h-2.5 rounded-full" style={{ width: `${score * 100}%` }}></div>
    </div>
);

export default function AiInsightsPage() {
    const [heuristics, setHeuristics] = useState<AggregatedHeuristic[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [ruleToCreate, setRuleToCreate] = useState<AutomationRuleCreate | null>(null);

    const fetchHeuristics = () => {
        setIsLoading(true);
        getLearnedHeuristics().then(setHeuristics).finally(() => setIsLoading(false));
    };

    useEffect(fetchHeuristics, []);

    const handlePromoteClick = (heuristic: AggregatedHeuristic) => {
        const prefilledRule: AutomationRuleCreate = {
            rule_name: `Auto-approve ${heuristic.exception_type.replace('Exception','')} for ${heuristic.vendor_name}`,
            vendor_name: heuristic.vendor_name,
            conditions: heuristic.learned_condition,
            action: heuristic.resolution_action,
            is_active: true,
            source: 'suggested'
        };
        setRuleToCreate(prefilledRule);
        setIsModalOpen(true);
    };

    const handleCreateRule = async (e: FormEvent) => {
        e.preventDefault();
        if (!ruleToCreate) return;
        try {
            await createAutomationRule(ruleToCreate);
            toast.success("Automation rule created successfully!");
            setIsModalOpen(false);
            setRuleToCreate(null);
        } catch (error) {
            toast.error(`Failed to create rule: ${error instanceof Error ? error.message : "Unknown error"}`);
        }
    };

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle>AI-Driven Automation Opportunities</CardTitle>
                    <CardDescription>The AI has identified these patterns from your team&apos;s actions. High-confidence patterns are ideal candidates for one-click automation.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="border rounded-lg">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Vendor & Exception</TableHead>
                              <TableHead>Learned Threshold</TableHead>
                              <TableHead className="w-[200px]">Confidence</TableHead>
                              <TableHead>Potential Impact</TableHead>
                              <TableHead className="text-right">Action</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {isLoading ? (
                                <TableRow><TableCell colSpan={5} className="text-center h-24">Analyzing patterns...</TableCell></TableRow>
                            ) : heuristics.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center h-32 text-gray-500">
                                        <p className="font-semibold">No Patterns Learned Yet</p>
                                        <p className="text-sm mt-1">As you resolve invoices in the workbench, the AI will identify recurring patterns and suggest automations here.</p>
                                    </TableCell>
                                </TableRow>
                            ) : heuristics.map(h => (
                              <TableRow key={h.id}>
                                <TableCell>
                                    <p className="font-medium">{h.vendor_name}</p>
                                    <Badge variant="warning">{h.exception_type.replace('Exception', '')}</Badge>
                                </TableCell>
                                <TableCell className="font-mono text-xs">{JSON.stringify(h.learned_condition)}</TableCell>
                                <TableCell>
                                    <div className="flex items-center gap-2">
                                        <ConfidenceBar score={h.confidence_score} />
                                        <span className="text-sm font-semibold">{(h.confidence_score * 100).toFixed(0)}%</span>
                                    </div>
                                </TableCell>
                                <TableCell>{h.potential_impact} invoices/mo</TableCell>
                                <TableCell className="text-right">
                                  <Button variant="secondary" size="sm" onClick={() => handlePromoteClick(h)} disabled={h.confidence_score < 0.8}>
                                    Promote <ArrowRight className="ml-2 h-4 w-4" />
                                  </Button>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>

            {ruleToCreate && (
                <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Promote to Automation Rule">
                    <form onSubmit={handleCreateRule} className="space-y-4">
                        <p className="text-sm text-gray-600">Review the suggested rule below. You can edit it before creating.</p>
                        <div>
                            <label className="block text-sm font-medium text-gray-dark">Rule Name</label>
                            <Input value={ruleToCreate.rule_name} onChange={e => setRuleToCreate({...ruleToCreate, rule_name: e.target.value})} required />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-dark">Conditions (JSON)</label>
                            <Textarea value={JSON.stringify(ruleToCreate.conditions, null, 2)} onChange={e => setRuleToCreate({...ruleToCreate, conditions: JSON.parse(e.target.value)})} rows={4} className="font-mono text-sm" />
                        </div>
                        <div className="flex justify-end gap-2">
                            <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                            <Button type="submit"><Sparkles className="mr-2 h-4 w-4" />Create Rule</Button>
                        </div>
                    </form>
                </Modal>
            )}
        </div>
    );
} 