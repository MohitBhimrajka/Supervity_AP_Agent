"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { type ExceptionSummaryItem } from '@/lib/api';

interface ExceptionChartProps {
  data: ExceptionSummaryItem[];
}

export const ExceptionChart = ({ data }: ExceptionChartProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Exception Analysis</CardTitle>
        <CardDescription>Breakdown of invoices currently needing review by exception type.</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" stroke="#888888" fontSize={12} allowDecimals={false} />
            <YAxis 
              type="category" 
              dataKey="name" 
              stroke="#888888" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false} 
              width={120} 
              interval={0}
            />
            <Tooltip
              cursor={{ fill: 'hsl(227, 85%, 97%)' }}
              contentStyle={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem' }}
            />
            <Bar dataKey="count" fill="var(--color-purple-accent)" name="Invoices" radius={[0, 4, 4, 0]} barSize={20} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}; 