import { Component, input, viewChild, ElementRef, effect } from '@angular/core';
import { Message } from '../../models/message.model';

@Component({
  selector: 'app-message-list',
  standalone: true,
  template: `
    <div #container class="messages">
      @for (m of messages(); track $index) {
        <div class="message" [class.user]="m.type === 'user'" [class.bot]="m.type === 'bot'">
          <div class="avatar">{{ m.type === 'user' ? '👤' : '🌱' }}</div>
          <div class="bubble">{{ m.content }}</div>
        </div>
      }
      @if (loading()) {
        <div class="message bot">
          <div class="avatar">🌱</div>
          <div class="bubble loading">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .messages {
      flex: 1; overflow-y: auto; padding: 1.5rem;
      display: flex; flex-direction: column; gap: 1rem;
    }
    .message { display: flex; align-items: flex-start; gap: 0.75rem; max-width: 80%; }
    .user { align-self: flex-end; flex-direction: row-reverse; }
    .bot { align-self: flex-start; }
    .avatar {
      width: 40px; height: 40px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.2rem; flex-shrink: 0;
    }
    .user .avatar { background: #8fbc8f; }
    .bot .avatar { background: #4a7c59; }
    .bubble {
      padding: 0.8rem 1rem; border-radius: 15px; line-height: 1.5; white-space: pre-wrap;
    }
    .user .bubble {
      background: #4a7c59; color: white; border-bottom-right-radius: 4px;
    }
    .bot .bubble {
      background: white; color: #2d5a3d; border: 1px solid #8fbc8f; border-bottom-left-radius: 4px;
    }
    .bubble.loading {
      display: flex; gap: 4px; align-items: center;
    }
    .dot {
      width: 8px; height: 8px; background: #4a7c59;
      border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both;
    }
    .dot:nth-child(2) { animation-delay: -0.16s; }
    .dot:nth-child(3) { animation-delay: -0.32s; }
    @keyframes bounce {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1); }
    }
  `]
})
export class MessageListComponent {
  messages = input.required<Message[]>();
  loading = input.required<boolean>();

  container = viewChild<ElementRef<HTMLDivElement>>('container');

  constructor() {
    effect(() => {
      this.messages();
      setTimeout(() => this.scrollToBottom(), 100);
    });
  }

  private scrollToBottom(): void {
    const el = this.container();
    if (el) el.nativeElement.scrollTop = el.nativeElement.scrollHeight;
  }
}