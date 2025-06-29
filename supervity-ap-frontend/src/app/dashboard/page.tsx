"use client";
import { useEffect, useState } from 'react';
import { type Kpis, getDashboardKpis, type Summary, getDashboardSummary } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { DollarSign, Zap, Clock, AlertCircle, TrendingUp, TrendingDown, FileInput, Filter, Check, Loader2 } from 'lucide-react';

const KpiCard = ({ title, value, icon: Icon, change, changeType }: { title: string, value: string | number, icon: React.ElementType, change?: string, changeType?: 'up' | 'down' }) => (
    <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">{title}</CardTitle>
            <Icon className="h-4 w-4 text-gray-700" />
        </CardHeader>
        <CardContent>
            <div className="text-3xl font-bold">{value}</div>
            {change && (
                <p className={`text-xs text-gray-500 mt-1 flex items-center ${changeType === 'up' ? 'text-green-success' : 'text-pink-destructive'}`}>
                    {changeType === 'up' ? <TrendingUp className="mr-1 h-3 w-3"/> : <TrendingDown className="mr-1 h-3 w-3"/>}
                    {change}
                </p>
            )}
        </CardContent>
    </Card>
);

const FunnelStep = ({ icon: Icon, title, value, colorClass }: { icon: React.ElementType, title: string, value: number, colorClass: string }) => (
    <div className="flex items-center p-4 bg-gray-50 rounded-lg">
        <div className={`p-3 rounded-full mr-4 ${colorClass}`}>
            <Icon className="w-6 h-6 text-white" />
        </div>
        <div>
            <p className="text-sm text-gray-500">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
        </div>
    </div>
);

export default function DashboardPage() {
    const [kpis, setKpis] = useState<Kpis | null>(null);
    const [summary, setSummary] = useState<Summary | null>(null);

    useEffect(() => {
        getDashboardKpis().then(setKpis).catch(console.error);
        getDashboardSummary().then(setSummary).catch(console.error);
    }, []);

    if (!kpis || !summary) {
        return <div className="p-4 flex items-center justify-center h-full"><Loader2 className="w-8 h-8 animate-spin" /></div>;
    }
    
    const efficiencyData = kpis.operational_efficiency;
    const financialData = kpis.financial_optimization;

    const discountData = [
        { name: 'Captured', value: parseFloat(financialData.discounts_captured.replace(/[$,]/g, '')), fill: '#85c20b' },
        { name: 'Missed', value: parseFloat(financialData.discounts_missed.replace(/[$,]/g, '')), fill: '#ff94a8' },
        { name: 'Pending', value: parseFloat(financialData.discounts_pending.replace(/[$,]/g, '')), fill: '#8289ec' },
    ];

    const vendorData = Object.entries(kpis.vendor_performance.top_vendors_by_exception_rate)
        .map(([name, rate]) => ({ name, rate: parseFloat(String(rate).replace('%','')) }))
        .sort((a,b) => b.rate - a.rate);

    // --- FIX IS HERE ---
    // The correct count is the touchless rate percentage of total processed invoices.
    const autoApprovedCount = Math.round(
        (efficiencyData.touchless_invoice_rate_percent / 100) * efficiencyData.total_processed_invoices
    );

    return (
        <div className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                <KpiCard title="Touchless Rate" value={`${efficiencyData.touchless_invoice_rate_percent.toFixed(1)}%`} icon={Zap} change="+5.2% from last month" changeType="up"/>
                <KpiCard title="Invoices in Review Queue" value={efficiencyData.invoices_in_review_queue} icon={AlertCircle} />
                <KpiCard title="Avg. Payment Time" value={`${financialData.days_payable_outstanding_proxy.toFixed(1)} days`} icon={Clock} change="-1.5 days" changeType="down"/>
                <KpiCard title="Discounts Captured" value={financialData.discounts_captured} icon={DollarSign} />
            </div>
            <Card>
                <CardHeader>
                    <CardTitle>Invoice Pipeline</CardTitle>
                    <CardDescription>A real-time overview of the document processing flow.</CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <FunnelStep icon={FileInput} title="Total Ingested" value={summary.total_invoices} colorClass="bg-cyan-accent" />
                    <FunnelStep icon={Filter} title="Pending Match" value={summary.pending_match} colorClass="bg-purple-accent" />
                    <FunnelStep icon={Check} title="Auto-Approved" value={autoApprovedCount} colorClass="bg-green-success" />
                    <FunnelStep icon={AlertCircle} title="Flagged for Review" value={summary.requires_review} colorClass="bg-orange-warning" />
                </CardContent>
            </Card>
            <div className="grid gap-6 lg:grid-cols-5">
                <Card className="lg:col-span-3">
                    <CardHeader>
                        <CardTitle>Top Vendors by Exception Rate</CardTitle>
                        <CardDescription>Vendors causing the most manual reviews.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={vendorData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                                <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}%`} />
                                <Tooltip cursor={{ fill: '#fafafa' }} contentStyle={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem' }}/>
                                <Bar dataKey="rate" fill="#ff9a5a" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
                <Card className="lg:col-span-2">
                    <CardHeader>
                        <CardTitle>Early Payment Discounts</CardTitle>
                        <CardDescription>Total value of discounts by status.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                             <PieChart>
                                <Pie data={discountData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} labelLine={false} label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}>
                                    {discountData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.fill} />)}
                                </Pie>
                                <Tooltip formatter={(value) => `$${Number(value).toFixed(2)}`} />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
} 