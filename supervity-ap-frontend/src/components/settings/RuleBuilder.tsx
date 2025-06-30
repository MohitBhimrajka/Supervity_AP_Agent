"use client";
import React from 'react';
import { type AutomationRuleCreate } from '@/lib/api';
import { Input } from '@/components/ui/Input';

// Define the structure of condition values
interface RuleConditions {
  field?: string;
  operator?: string;
  value?: string | number;
}

const FIELD_OPTIONS = [
    { value: 'grand_total', label: 'Invoice Total', type: 'number' },
    { value: 'vendor_name', label: 'Vendor Name', type: 'text' },
    { value: 'line_item_count', label: 'Line Item Count', type: 'number' },
    // Add more fields as needed, e.g., 'subtotal', 'tax'
];

const OPERATOR_OPTIONS: Record<string, { value: string; label: string }[]> = {
    number: [
        { value: '>', label: '>' },
        { value: '<', label: '<' },
        { value: '>=', label: '>=' },
        { value: '<=', label: '<=' },
        { value: '==', label: '=' },
    ],
    text: [
        { value: 'equals', label: 'Equals' },
        { value: 'contains', label: 'Contains' },
        { value: 'not_equals', label: 'Does Not Equal' },
    ],
};

interface RuleBuilderProps {
  rule: AutomationRuleCreate;
  onRuleChange: (updatedRule: AutomationRuleCreate) => void;
}

export const RuleBuilder = ({ rule, onRuleChange }: RuleBuilderProps) => {
  const handleConditionChange = (
    key: 'field' | 'operator' | 'value',
    value: string | number
  ) => {
    const currentConditions = rule.conditions as RuleConditions || {};
    const newConditions = { ...currentConditions, [key]: value };
    // If the field changes, reset the operator and value
    if (key === 'field') {
        newConditions.operator = '';
        newConditions.value = '';
    }
    onRuleChange({ ...rule, conditions: newConditions });
  };
  
  const conditions = rule.conditions as RuleConditions || {};
  const selectedField = FIELD_OPTIONS.find(f => f.value === conditions.field);

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-dark">Rule Name</label>
        <Input 
          value={rule.rule_name} 
          onChange={e => onRuleChange({ ...rule, rule_name: e.target.value })} 
          required 
          placeholder="e.g., Auto-approve small invoices"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-dark">Vendor Name (Optional)</label>
        <Input 
          value={rule.vendor_name ?? ''} 
          onChange={e => onRuleChange({ ...rule, vendor_name: e.target.value || null })} 
          placeholder="e.g., ArcelorMittal"
        />
      </div>
      <div className="p-4 border rounded-md bg-gray-50">
        <label className="block text-sm font-medium text-gray-dark mb-2">Conditions</label>
        <div className="flex items-center gap-2">
            <span className="font-semibold">IF</span>
            <select
              value={conditions.field || ''}
              onChange={e => handleConditionChange('field', e.target.value)}
              className="flex h-10 w-full items-center justify-between rounded-md border border-gray-light bg-white px-3 py-2 text-sm"
            >
                <option value="" disabled>Select a field...</option>
                {FIELD_OPTIONS.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
            
            <select
              value={conditions.operator || ''}
              onChange={e => handleConditionChange('operator', e.target.value)}
              className="flex h-10 w-full items-center justify-between rounded-md border border-gray-light bg-white px-3 py-2 text-sm"
              disabled={!selectedField}
            >
                <option value="" disabled>Select operator...</option>
                {selectedField && OPERATOR_OPTIONS[selectedField.type].map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>

            <Input
                type={selectedField?.type || 'text'}
                value={conditions.value || ''}
                onChange={e => handleConditionChange('value', e.target.value)}
                className="bg-white"
                disabled={!selectedField}
            />
        </div>
      </div>
    </div>
  );
}; 