'use client';

import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Minimize2, Maximize2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/toast-provider';
import { useSession } from 'next-auth/react';

interface SupportMessage {
  id: string;
  ticket_id: string;
  user_id: string;
  message: string;
  is_internal: boolean;
  created_at: string;
}

interface SupportTicket {
  id: string;
  subject: string;
  status: string;
  priority: string;
  created_at: string;
}

export function SupportChatWidget() {
  const { data: session } = useSession();
  const { success, error: showError } = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [message, setMessage] = useState('');
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [messages, setMessages] = useState<SupportMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  useEffect(() => {
    if (isOpen && selectedTicket) {
      loadMessages(selectedTicket.id);
    }
  }, [isOpen, selectedTicket]);

  useEffect(() => {
    if (isOpen) {
      loadTickets();
    }
  }, [isOpen]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadTickets = async () => {
    try {
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/v1/support/tickets`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setTickets(data);
        if (data.length > 0 && !selectedTicket) {
          setSelectedTicket(data[0]);
        }
      }
    } catch (err) {
      console.error('Failed to load tickets:', err);
    }
  };

  const loadMessages = async (ticketId: string) => {
    try {
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/v1/support/tickets/${ticketId}/messages`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setMessages(data.filter((m: SupportMessage) => !m.is_internal));
      }
    } catch (err) {
      console.error('Failed to load messages:', err);
    }
  };

  const handleSendMessage = async () => {
    if (!message.trim() || !selectedTicket) return;

    try {
      setIsLoading(true);
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/v1/support/tickets/${selectedTicket.id}/messages`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: message.trim()
        })
      });

      if (response.ok) {
        const data = await response.json();
        setMessages([...messages, data]);
        setMessage('');
        success('Message sent', 'Your message has been sent to support');
      } else {
        const data = await response.json();
        showError('Send Failed', data.detail || 'Failed to send message');
      }
    } catch (err: any) {
      showError('Send Error', err.message || 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTicket = async (subject: string, description: string) => {
    try {
      setIsLoading(true);
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/v1/support/tickets`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          subject,
          description,
          priority: 'medium'
        })
      });

      if (response.ok) {
        const data = await response.json();
        setTickets([data, ...tickets]);
        setSelectedTicket(data);
        success('Ticket created', 'Support ticket created successfully');
      } else {
        const data = await response.json();
        showError('Create Failed', data.detail || 'Failed to create ticket');
      }
    } catch (err: any) {
      showError('Create Error', err.message || 'Failed to create ticket');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <Button
          onClick={() => setIsOpen(true)}
          size="lg"
          className="rounded-full shadow-lg"
        >
          <MessageCircle className="h-5 w-5 mr-2" />
          Support
        </Button>
      </div>
    );
  }

  return (
    <div className={`fixed ${isMinimized ? 'bottom-4 right-4' : 'bottom-4 right-4'} z-50 w-96 ${isMinimized ? 'h-auto' : 'h-[600px]'} transition-all`}>
      <Card className="shadow-2xl flex flex-col h-full">
        <CardHeader className="pb-3 flex-shrink-0">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Support Chat</CardTitle>
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsMinimized(!isMinimized)}
              >
                {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        
        {!isMinimized && (
          <>
            {tickets.length === 0 ? (
              <CardContent className="flex-1 flex flex-col items-center justify-center p-6">
                <p className="text-muted-foreground text-center mb-4">
                  No support tickets yet. Create one to get started.
                </p>
                <Button
                  onClick={() => handleCreateTicket('New Support Request', 'I need help with...')}
                  variant="outline"
                >
                  Create Ticket
                </Button>
              </CardContent>
            ) : (
              <>
                {!selectedTicket && (
                  <CardContent className="flex-1 overflow-y-auto">
                    <div className="space-y-2">
                      {tickets.map((ticket) => (
                        <div
                          key={ticket.id}
                          className="p-3 border rounded cursor-pointer hover:bg-muted"
                          onClick={() => setSelectedTicket(ticket)}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-sm">{ticket.subject}</span>
                            <Badge variant={ticket.status === 'resolved' ? 'default' : 'secondary'}>
                              {ticket.status}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {new Date(ticket.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                )}

                {selectedTicket && (
                  <>
                    <CardContent className="flex-1 overflow-y-auto space-y-4 p-4">
                      <div className="flex items-center justify-between pb-2 border-b">
                        <div>
                          <h3 className="font-medium">{selectedTicket.subject}</h3>
                          <p className="text-xs text-muted-foreground">
                            {new Date(selectedTicket.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedTicket(null)}
                        >
                          Back
                        </Button>
                      </div>

                      <div className="space-y-3">
                        {messages.map((msg) => (
                          <div
                            key={msg.id}
                            className={`p-3 rounded-lg ${
                              msg.user_id === (session as any)?.user?.id
                                ? 'bg-primary text-primary-foreground ml-auto max-w-[80%]'
                                : 'bg-muted max-w-[80%]'
                            }`}
                          >
                            <p className="text-sm">{msg.message}</p>
                            <p className="text-xs opacity-70 mt-1">
                              {new Date(msg.created_at).toLocaleTimeString()}
                            </p>
                          </div>
                        ))}
                        <div ref={messagesEndRef} />
                      </div>
                    </CardContent>

                    <CardContent className="flex-shrink-0 border-t p-4">
                      <div className="flex gap-2">
                        <Input
                          value={message}
                          onChange={(e) => setMessage(e.target.value)}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              handleSendMessage();
                            }
                          }}
                          placeholder="Type your message..."
                          disabled={isLoading}
                        />
                        <Button
                          onClick={handleSendMessage}
                          disabled={!message.trim() || isLoading}
                        >
                          <Send className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </>
                )}
              </>
            )}
          </>
        )}
      </Card>
    </div>
  );
}

