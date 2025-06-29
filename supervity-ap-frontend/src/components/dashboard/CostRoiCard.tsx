"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { type CostRoiMetrics } from '@/lib/api';
import { TrendingUp } from 'lucide-react';

interface CostRoiCardProps {
    data: CostRoiMetrics;
}

const MetricRow = ({ label, value, isBold = false }: { label: string, value: string, isBold?: boolean }) => (
    <div className={`flex justify-between items-center py-2 text-sm ${isBold ? 'font-bold text-black' : 'font-medium text-gray-700'}`}>
        <span>{label}</span>
        <span>{value}</span>
    </div>
);

export const CostRoiCard = ({ data }: CostRoiCardProps) => {
    return (
        <Card>
            <CardHeader>
                <CardTitle>AI ROI Analysis</CardTitle>
                <CardDescription>
                    Evaluating the financial impact of the AP Agent.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div>
                    <h4 className="font-semibold mb-2 text-black">Investment (To Date)</h4>
                    <MetricRow label="Agent Processing Costs" value={`$${data.agent_expense.toFixed(2)}`} />
                    <MetricRow label="Est. Monthly Infra Cost" value={`$${data.infra_cost_monthly.toFixed(2)}`} />
                </div>
                 <div>
                    <h4 className="font-semibold mb-2 text-black">Return (To Date)</h4>
                    <MetricRow label="Value of Time Saved" value={`$${data.time_saved_value.toFixed(2)}`} />
                    <MetricRow label="Discounts Captured" value={`$${data.discounts_captured_value.toFixed(2)}`} />
                    <MetricRow label="Total Return" value={`$${data.total_return_todate.toFixed(2)}`} isBold={true} />
                </div>
                <div className="bg-blue-primary/10 p-4 rounded-lg">
                     <div className="flex justify-between items-center">
                        <div className="flex items-center font-bold text-lg text-blue-primary">
                            <TrendingUp className="w-6 h-6 mr-2" />
                            <span>Total ROI to Date</span>
                        </div>
                        <span className={`text-2xl font-extrabold ${data.ai_roi_todate >= 0 ? 'text-green-success' : 'text-pink-destructive'}`}>
                          ${data.ai_roi_todate.toFixed(2)}
                        </span>
                     </div>
                </div>
            </CardContent>
        </Card>
    );
}; 