import { Injectable, signal } from '@angular/core';
import { Message } from '../models/message.model';
import { Conversation } from '../components/sidebar/sidebar.component';

const API_URL = 'http://localhost:8000';

@Injectable({ providedIn: 'root' })
export class ChatService {
  messages = signal<Message[]>([]);
  isLoading = signal(false);
  threadId = signal<string>('default-thread');
  conversations = signal<Conversation[]>([]);

  private activeController: AbortController | null = null;
  private isStreaming = signal(false);

  async loadConversations(): Promise<void> {
    try {
      const res = await fetch(`${API_URL}/conversations`);
      if (!res.ok) return;
      const data = await res.json();
      this.conversations.set(data.conversations);
    } catch (e) {
      console.error('Error loading conversations:', e);
    }
  }

  cancelStream(): void {
    if (this.activeController) {
      this.activeController.abort();
      this.activeController = null;
    }
    this.isStreaming.set(false);
    this.isLoading.set(false);
  }

  streaming() {
    return this.isStreaming.asReadonly();
  }

  async sendMessage(content: string): Promise<void> {
    if (!content.trim() || this.isLoading()) return;

    if (this.activeController) {
      this.activeController.abort();
      this.activeController = null;
    }

    const input = content.trim();
    this.messages.update(msgs => [...msgs, { type: 'user', content: input }]);
    this.isLoading.set(true);
    this.isStreaming.set(true);

    const controller = new AbortController();
    this.activeController = controller;
    let botResponse = '';

    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, thread_id: this.threadId() }),
        signal: controller.signal,
      });

      if (!response.ok) throw new Error('Error en conexión');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder('utf-8');

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const text = decoder.decode(value, { stream: true });
          const lines = text.split('\n').filter(l => l.startsWith('data: '));
          for (const line of lines) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'message') botResponse += data.content;
              else if (data.type === 'error') botResponse += `\n[Error: ${data.content}]`;
              else if (data.type === 'done') break;
            } catch (e) {
              console.error(e);
            }
          }
        }
        const tail = decoder.decode();
        if (tail) {
          const lines = tail.split('\n').filter(l => l.startsWith('data: '));
          for (const line of lines) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'message') botResponse += data.content;
            } catch (e) {
              console.error(e);
            }
          }
        }
      }

      if (this.activeController === controller && botResponse) {
        this.messages.update(msgs => [...msgs, { type: 'bot', content: botResponse }]);
        await this.loadConversations();
      }
    } catch (e: any) {
      if (e?.name === 'AbortError') {
        if (botResponse.length > 0) {
          this.messages.update(msgs => [...msgs, { type: 'bot', content: botResponse }]);
        }
      } else {
        this.messages.update(msgs => [...msgs, {
          type: 'bot',
          content: 'Lo siento, ha ocurrido un error al conectar con el servidor.',
        }]);
      }
    } finally {
      if (this.activeController === controller) {
        this.activeController = null;
      }
      this.isLoading.set(false);
      this.isStreaming.set(false);
    }
  }

  async newChat(): Promise<void> {
    this.cancelStream();
    try {
      const res = await fetch(`${API_URL}/conversations`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        this.threadId.set(data.thread_id);
      } else {
        this.threadId.set(`thread-${Date.now()}`);
      }
    } catch {
      this.threadId.set(`thread-${Date.now()}`);
    }
    this.messages.set([]);
    await this.loadConversations();
  }

  async selectConversation(threadId: string): Promise<void> {
    this.cancelStream();
    this.threadId.set(threadId);
    await this.loadHistory();
  }

  async loadHistory(): Promise<void> {
    try {
      const res = await fetch(`${API_URL}/conversations/${this.threadId()}`);
      if (!res.ok) return;
      const data = await res.json();
      const loaded: Message[] = [];
      for (const msg of data.messages) {
        if (msg.type === 'HumanMessage') loaded.push({ type: 'user', content: msg.content });
        else if (msg.type === 'AIMessage') loaded.push({ type: 'bot', content: msg.content });
      }
      this.messages.set(loaded);
    } catch (e) {
      console.error(e);
    }
  }

  async deleteConversation(threadId: string): Promise<void> {
    try {
      await fetch(`${API_URL}/conversations/${threadId}`, { method: 'DELETE' });
      this.conversations.update(convs => convs.filter(c => c.thread_id !== threadId));
      if (this.threadId() === threadId) {
        await this.newChat();
      }
    } catch (e) {
      console.error('Error deleting conversation:', e);
    }
  }
}
