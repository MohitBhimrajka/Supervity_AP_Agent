"use client";
import { useState } from 'react';
import { type ExceptionSummaryItem, type InvoiceSummary, getInvoicesByCategory } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { InvoiceListModal } from './InvoiceListModal';
import toast from 'react-hot-toast';
import { Loader2 } from 'lucide-react';

const COLORS = ['#FF8042', '#00C49F', '#FFBB28', '#0088FE', '#A4DE6C', '#8884d8'];

export const ExceptionChart = ({ data }: { data: ExceptionSummaryItem[] }) => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalInvoices, setModalInvoices] = useState<InvoiceSummary[]>([]);
    const [modalCategory, setModalCategory] = useState("");
    const [isModalLoading, setIsModalLoading] = useState(false);

    const handleBarClick = async (data: unknown) => {
        if (!data || typeof data !== 'object' || !('name' in data)) return;
        
        const categoryName = (data as { name: string }).name;

        setIsModalLoading(true);
        setModalCategory(categoryName);
        setIsModalOpen(true);
        
        try {
            const invoices = await getInvoicesByCategory(categoryName);
            setModalInvoices(invoices);
        } catch {
            toast.error(`Failed to fetch invoices for ${categoryName}`);
            setIsModalOpen(false); // Close modal on error
        } finally {
            setIsModalLoading(false);
        }
    };

    return (
        <>
            <Card className="h-full">
                <CardHeader>
                    <CardTitle>Live Exception Analysis</CardTitle>
                    <CardDescription>Click a bar to drill down into specific invoices.</CardDescription>
                </CardHeader>
                <CardContent>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 10, bottom: 5 }} barCategoryGap="20%">
                            <XAxis type="number" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                            <YAxis type="category" dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} width={120} interval={0} />
                            <Tooltip
                                cursor={{ fill: 'rgba(240, 240, 240, 0.5)' }}
                                contentStyle={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem' }}
                                labelStyle={{ fontWeight: 'bold' }}
                                formatter={(value: number) => [value, 'Invoices']}
                            />
                            <Bar dataKey="count" radius={[0, 4, 4, 0]} className="cursor-pointer" onClick={handleBarClick}>
                                {data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>

            <InvoiceListModal 
                isOpen={isModalOpen} 
                onClose={() => setIsModalOpen(false)} 
                title={`Invoices with Exception: ${modalCategory}`}
            >
                {isModalLoading ? (
                    <div className="flex justify-center items-center h-48">
                        <Loader2 className="w-8 h-8 animate-spin" />
                    </div>
                ) : (
                   <InvoiceListModal.Content invoices={modalInvoices} />
                )}
            </InvoiceListModal>
        </>
    );
}; 