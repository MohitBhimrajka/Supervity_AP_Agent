"use client";
import { type CostRoiMetrics } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { ArrowDown, ArrowUp } from 'lucide-react';

const Metric = ({ label, value, colorClass }: { label: string, value: string, colorClass?: string }) => (
    <div className="flex justify-between items-center text-sm py-2 border-b last:border-b-0">
        <span className="text-gray-500">{label}</span>
        <span className={`font-semibold ${colorClass}`}>{value}</span>
    </div>
);

export const CostRoiCard = ({ data }: { data: CostRoiMetrics }) => {
    const roiPercent = data.total_cost_for_period > 0 
        ? ((data.total_return_for_period - data.total_cost_for_period) / data.total_cost_for_period * 100)
        : 0;

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle>Automation ROI</CardTitle>
                <CardDescription>Estimated cost vs. savings for selected period.</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="flex justify-center items-center my-4">
                    <div className={`flex items-center text-4xl font-bold ${roiPercent >= 0 ? 'text-green-success' : 'text-pink-destructive'}`}>
                        {roiPercent >= 0 ? <ArrowUp className="h-8 w-8 mr-2"/> : <ArrowDown className="h-8 w-8 mr-2"/>}
                        {roiPercent.toFixed(1)}%
                    </div>
                </div>
                <div className="space-y-1">
                    <Metric label="Total Return" value={`$${data.total_return_for_period.toFixed(2)}`} colorClass="text-green-success" />
                    <Metric label="Total Cost" value={`$${data.total_cost_for_period.toFixed(2)}`} colorClass="text-pink-destructive" />
                </div>
            </CardContent>
        </Card>
    );
}; 