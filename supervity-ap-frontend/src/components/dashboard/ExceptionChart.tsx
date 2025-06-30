"use client";
import { useState } from 'react';
import { type ExceptionSummaryItem, type Invoice, getInvoicesByCategory } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { InvoiceListModal } from './InvoiceListModal';
import toast from 'react-hot-toast';

const COLORS = ['#FF8042', '#00C49F', '#FFBB28', '#0088FE'];

export const ExceptionChart = ({ data }: { data: ExceptionSummaryItem[] }) => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalInvoices, setModalInvoices] = useState<Invoice[]>([]);
    const [modalCategory, setModalCategory] = useState("");

    const handleBarClick = async (data: unknown) => {
        if (!data || typeof data !== 'object' || !('name' in data)) return;
        
        const category = (data as { name: string }).name;
        setModalCategory(category);
        
        try {
            const invoices = await getInvoicesByCategory(category);
            setModalInvoices(invoices);
            setIsModalOpen(true);
        } catch {
            toast.error(`Failed to fetch invoices for ${category}`);
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
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, left: 20, bottom: 5 }} onClick={handleBarClick}>
                            <XAxis type="number" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis type="category" dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} width={120} />
                            <Tooltip cursor={{ fill: '#fafafa' }} contentStyle={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem' }}/>
                            <Bar dataKey="count" fill="#8884d8" radius={[0, 4, 4, 0]} className="cursor-pointer">
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
                invoices={modalInvoices}
                category={modalCategory}
            />
        </>
    );
}; 