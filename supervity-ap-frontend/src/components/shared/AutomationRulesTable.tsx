"use client";
import { useState, useEffect, FormEvent } from 'react';
import { 
    getAutomationRules, 
    createAutomationRule,
    updateAutomationRule,
    deleteAutomationRule,
    type AutomationRule,
    type AutomationRuleCreate 
} from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Modal } from '../ui/Modal';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';
import { Pencil, Trash2, PlusCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const initialFormData: AutomationRuleCreate = {
    rule_name: '',
    vendor_name: null,
    conditions: { field: '', operator: '', value: '' },
    action: 'approve',
    is_active: true,
    source: 'user'
};

export const AutomationRulesTable = () => {
    const [rules, setRules] = useState<AutomationRule[]>([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingRule, setEditingRule] = useState<AutomationRule | null>(null);
    const [formData, setFormData] = useState<AutomationRuleCreate>(initialFormData);

    const fetchRules = () => getAutomationRules().then(setRules);

    useEffect(() => {
        fetchRules();
    }, []);

    const openModalForEdit = (rule: AutomationRule) => {
        setEditingRule(rule);
        setFormData({
            ...rule,
            conditions: typeof rule.conditions === 'string' ? JSON.parse(rule.conditions) : rule.conditions,
        });
        setIsModalOpen(true);
    };

    const openModalForNew = () => {
        setEditingRule(null);
        setFormData(initialFormData);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setEditingRule(null);
    };

    const handleDelete = async (id: number) => {
        if (window.confirm('Are you sure you want to delete this rule?')) {
            try {
                await deleteAutomationRule(id);
                toast.success('Rule deleted!');
                fetchRules();
            } catch {
                toast.error('Failed to delete rule.');
            }
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        const apiCall = editingRule
            ? updateAutomationRule(editingRule.id, formData)
            : createAutomationRule(formData);
        
        try {
            await apiCall;
            toast.success(`Rule ${editingRule ? 'updated' : 'created'}!`);
            fetchRules();
            closeModal();
        } catch (err) {
            toast.error(`Failed to save rule: ${err instanceof Error ? err.message : "Unknown error"}`);
        }
    };
    
    return (
        <>
            <div className="flex justify-end mb-4">
                <Button onClick={openModalForNew}>
                    <PlusCircle className="mr-2 h-4 w-4" /> Add Automation Rule
                </Button>
            </div>
            <div className="border rounded-lg">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Rule Name</TableHead>
                      <TableHead>Vendor</TableHead>
                      <TableHead>Condition</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rules.map(rule => (
                      <TableRow key={rule.id}>
                        <TableCell className="font-medium">{rule.rule_name}</TableCell>
                        <TableCell>{rule.vendor_name || 'Any'}</TableCell>
                        <TableCell className="font-mono text-xs">{String(rule.conditions.field ?? '')} {String(rule.conditions.operator ?? '')} {String(rule.conditions.value ?? '')}</TableCell>
                        <TableCell><Badge variant="success">{rule.action}</Badge></TableCell>
                        <TableCell className="text-right">
                            <Button variant="ghost" size="sm" onClick={() => openModalForEdit(rule)}><Pencil className="h-4 w-4" /></Button>
                            <Button variant="ghost" size="sm" className="text-pink-destructive hover:text-pink-destructive" onClick={() => handleDelete(rule.id)}><Trash2 className="h-4 w-4" /></Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
            </div>

            <Modal isOpen={isModalOpen} onClose={closeModal} title={editingRule ? 'Edit Rule' : 'Add New Rule'}>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-dark">Rule Name</label>
                        <Input value={formData.rule_name} onChange={e => setFormData({...formData, rule_name: e.target.value})} required />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-dark">Vendor Name (Optional)</label>
                        <Input value={formData.vendor_name ?? ''} onChange={e => setFormData({...formData, vendor_name: e.target.value || null})} />
                    </div>
                     <div>
                        <label className="block text-sm font-medium text-gray-dark">Conditions (JSON)</label>
                        <Textarea 
                            value={JSON.stringify(formData.conditions, null, 2)} 
                            onChange={e => {
                                try {
                                    const parsed = JSON.parse(e.target.value);
                                    setFormData({...formData, conditions: parsed});
                                } catch {
                                    // Handle invalid JSON, maybe show an error
                                }
                            }} 
                            rows={4}
                            className="font-mono text-sm"
                        />
                         <p className="text-xs text-gray-medium mt-1">Example: {`{"field": "grand_total", "operator": "<", "value": 500}`}</p>
                    </div>
                    <div className="flex justify-end gap-2">
                        <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
                        <Button type="submit">Save Rule</Button>
                    </div>
                </form>
            </Modal>
        </>
    );
}; 