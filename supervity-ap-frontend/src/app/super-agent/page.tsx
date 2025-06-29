"use client";
import { useState, useRef, useEffect } from 'react';
import { type CopilotResponse, postToCopilot } from '@/lib/api';
import { useAppContext } from '@/lib/AppContext';
import { Bot, User, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';
import { BotMessageRenderer } from '@/components/shared/BotMessageRenderer';
import toast from 'react-hot-toast';

interface Message {
  sender: 'user' | 'bot';
  content: string;
  data?: unknown | null;
  uiAction?: string;
}

export default function SuperAgentPage() {
    const { currentInvoiceId } = useAppContext();
    const [messages, setMessages] = useState<Message[]>([
        { sender: 'bot', content: "Hello! I'm your AP Automation co-pilot. How can I assist you today?"}
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<null | HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSendMessage = async () => {
        if (!input.trim() || isLoading) return;
        
        const userMessage: Message = { sender: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response: CopilotResponse = await postToCopilot({ 
                message: input,
                current_invoice_id: currentInvoiceId,
            });
            const botMessage: Message = { 
                sender: 'bot', 
                content: response.responseText,
                data: response.data,
                uiAction: response.uiAction
            };
            setMessages(prev => [...prev, botMessage]);
            
            if (response.uiAction === 'SHOW_TOAST_SUCCESS') {
                toast.success(response.responseText);
            }
        } catch (error) {
            const errorMessage: Message = { 
                sender: 'bot', 
                content: 'Sorry, I encountered an error. Please try again.' 
            };
            setMessages(prev => [...prev, errorMessage]);
            toast.error(`Failed to get response: ${error instanceof Error ? error.message : 'Please try again'}`);
        } finally {
            setIsLoading(false);
        }
    };
    
    return (
        <div className="flex flex-col h-full bg-white rounded-lg border">
            {currentInvoiceId && (
                <div className="p-2 text-center text-sm bg-purple-600/10 text-purple-600 border-b">
                    Context: Currently viewing Invoice <strong>{currentInvoiceId}</strong>
                </div>
            )}
            <div className="flex-grow p-6 overflow-y-auto">
                <div className="space-y-6">
                    {messages.map((msg, index) => (
                        <div key={index} className={`flex items-start gap-4 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
                            {msg.sender === 'bot' && <div className="w-8 h-8 rounded-full bg-blue-light flex items-center justify-center shrink-0"><Bot className="w-5 h-5 text-blue-primary" /></div>}
                            <div className={`p-4 rounded-lg max-w-2xl ${msg.sender === 'user' ? 'bg-blue-primary text-white' : 'bg-gray-100'}`}>
                                {msg.sender === 'bot' ? (
                                    <BotMessageRenderer 
                                        content={msg.content}
                                        uiAction={msg.uiAction}
                                        data={msg.data}
                                    />
                                ) : (
                                    <p>{msg.content}</p>
                                )}
                            </div>
                            {msg.sender === 'user' && <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0"><User className="w-5 h-5 text-gray-800" /></div>}
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex items-start gap-4">
                            <div className="w-8 h-8 rounded-full bg-blue-light flex items-center justify-center shrink-0"><Bot className="w-5 h-5 text-blue-primary" /></div>
                            <div className="p-4 rounded-lg bg-gray-100 text-gray-800 flex items-center">
                                <Loader2 className="w-5 h-5 animate-spin"/>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>
            <div className="p-4 border-t bg-white">
                <div className="flex gap-4">
                    <Textarea 
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } }}
                        placeholder="Ask about KPIs, invoices, or vendors..."
                        className="flex-grow resize-none"
                    />
                    <Button onClick={handleSendMessage} disabled={isLoading || !input.trim()}>Send</Button>
                </div>
            </div>
        </div>
    );
} 