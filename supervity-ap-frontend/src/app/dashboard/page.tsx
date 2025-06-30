"use client";
import { useEffect, useState, useCallback } from 'react';
import { 
    type Kpis, getDashboardKpis, 
    type Summary, getDashboardSummary, 
    type ExceptionSummaryItem, getExceptionSummary,
    type CostRoiMetrics, getCostRoiMetrics,
    type DateRange
} from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Zap, Clock, AlertCircle, TrendingUp, TrendingDown, FileInput, Filter, Check, Loader2, DollarSign } from 'lucide-react';
import { ExceptionChart } from '@/components/dashboard/ExceptionChart';
import { CostRoiCard } from '@/components/dashboard/CostRoiCard';
import { StaggeredFadeIn, FadeInItem } from '@/components/dashboard/StaggeredFadeIn';
import { DateRangePicker } from '@/components/ui/DateRangePicker';
import { subDays, format } from 'date-fns';
import CountUp from 'react-countup';

const KpiCard = ({ title, value, icon: Icon, change, changeType, isCurrency = false }: { title: string, value: number, icon: React.ElementType, change?: string, changeType?: 'up' | 'down', isCurrency?: boolean }) => (
    <Card className="transform hover:scale-105 hover:shadow-lg transition-all duration-300">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">{title}</CardTitle>
            <Icon className="h-4 w-4 text-gray-700" />
        </CardHeader>
        <CardContent>
            <div className="text-3xl font-bold">
                <CountUp 
                    start={0} 
                    end={value} 
                    duration={2} 
                    separator="," 
                    decimals={isCurrency || !Number.isInteger(value) ? 2 : 0}
                    prefix={isCurrency ? '$' : ''}
                />
            </div>
            {change && (
                <p className={`text-xs mt-1 flex items-center ${changeType === 'up' ? 'text-green-success' : 'text-pink-destructive'}`}>
                    {changeType === 'up' ? <TrendingUp className="mr-1 h-3 w-3"/> : <TrendingDown className="mr-1 h-3 w-3"/>}
                    {change} vs. previous period
                </p>
            )}
        </CardContent>
    </Card>
);

export default function DashboardPage() {
    const [dateRange, setDateRange] = useState<DateRange>({ from: format(subDays(new Date(), 30), 'yyyy-MM-dd'), to: format(new Date(), 'yyyy-MM-dd') });
    const [kpis, setKpis] = useState<Kpis | null>(null);
    const [summary, setSummary] = useState<Summary | null>(null);
    const [exceptionData, setExceptionData] = useState<ExceptionSummaryItem[] | null>(null);
    const [costRoiData, setCostRoiData] = useState<CostRoiMetrics | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchData = useCallback(() => {
        setIsLoading(true);
        Promise.all([
            getDashboardKpis(dateRange),
            getDashboardSummary(dateRange),
            getExceptionSummary(dateRange),
            getCostRoiMetrics(dateRange)
        ]).then(([kpisData, summaryData, exceptionData, costRoiData]) => {
            setKpis(kpisData);
            setSummary(summaryData);
            setExceptionData(exceptionData);
            setCostRoiData(costRoiData);
        }).catch(error => {
            console.error("Failed to load dashboard data:", error);
        }).finally(() => setIsLoading(false));
    }, [dateRange]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    if (isLoading || !kpis || !summary || !exceptionData || !costRoiData) {
        return <div className="p-4 flex items-center justify-center h-full"><Loader2 className="w-8 h-8 animate-spin" /></div>;
    }
    
    const efficiencyData = kpis.operational_efficiency;
    const financialData = kpis.financial_optimization;
    const touchlessChange = efficiencyData.touchless_rate_change;
    
    // Parse values for CountUp
    const discountsCapturedValue = parseFloat(financialData.discounts_captured.replace(/[$,]/g, ''));

    const funnelData = [
        { title: 'Total Ingested', value: summary.total_invoices, icon: FileInput, color: 'bg-cyan-accent' },
        { title: 'Pending Match', value: summary.pending_match, icon: Filter, color: 'bg-purple-accent' },
        { title: 'Flagged for Review', value: summary.requires_review, icon: AlertCircle, color: 'bg-orange-warning' },
        { title: 'Touchless Approved', value: summary.auto_approved, icon: Check, color: 'bg-green-success' },
    ];
    
    return (
        <StaggeredFadeIn>
            <div className="space-y-6">
                <FadeInItem>
                    <div className="flex justify-between items-center">
                        <h1 className="text-2xl font-bold text-gray-800">AP Dashboard</h1>
                        <DateRangePicker value={dateRange} onValueChange={setDateRange} />
                    </div>
                </FadeInItem>

                <FadeInItem>
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                        <KpiCard title="Touchless Rate" value={efficiencyData.touchless_invoice_rate_percent} icon={Zap} change={`${touchlessChange.toFixed(1)}%`} changeType={touchlessChange >= 0 ? 'up' : 'down'} />
                        <KpiCard title="Avg. Handling Time" value={efficiencyData.avg_exception_handling_time_hours} icon={Clock} />
                        <KpiCard title="Invoices in Review" value={efficiencyData.invoices_in_review_queue} icon={AlertCircle} />
                        <KpiCard title="Discounts Captured" value={discountsCapturedValue} icon={DollarSign} isCurrency={true} />
                    </div>
                </FadeInItem>
                
                <FadeInItem>
                    <Card>
                        <CardHeader>
                            <CardTitle>Invoice Pipeline</CardTitle>
                            <CardDescription>A real-time overview of the document processing flow for the selected period.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="relative w-full max-w-3xl mx-auto py-4">
                                {funnelData.map((step, index) => (
                                    <div key={step.title} className="relative z-10 flex justify-center mb-2">
                                        <div className="w-full flex justify-center" style={{ transform: `scale(${1 - (index * 0.12)})`}}>
                                            <div className={`w-full max-w-lg ${step.color} text-white rounded-lg p-3 shadow-lg flex items-center justify-between`}>
                                                <div className="flex items-center">
                                                    <div className="bg-white/20 p-2 rounded-full mr-4"><step.icon className="w-6 h-6" /></div>
                                                    <p className="font-semibold">{step.title}</p>
                                                </div>
                                                <div className="text-2xl font-bold">{step.value}</div>
                                            </div>
                                        </div>
                                        {/* Connecting Line */}
                                        {index < funnelData.length - 1 && (
                                            <div className="absolute -bottom-5 left-1/2 transform -translate-x-1/2 w-px h-6 bg-gray-300 z-0"></div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </FadeInItem>

                <FadeInItem>
                    <div className="grid gap-6 lg:grid-cols-5">
                        <div className="lg:col-span-2">
                            <CostRoiCard data={costRoiData} />
                        </div>
                        <div className="lg:col-span-3">
                            <ExceptionChart data={exceptionData} />
                        </div>
                    </div>
                </FadeInItem>
            </div>
        </StaggeredFadeIn>
    );
} 