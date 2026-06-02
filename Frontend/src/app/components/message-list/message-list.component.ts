import { Component, ElementRef, OnDestroy, effect, inject, input, viewChild } from '@angular/core';
import { Message } from '../../models/message.model';
import { MessageBubbleComponent } from '../message-bubble/message-bubble.component';

@Component({
  selector: 'app-message-list',
  standalone: true,
  imports: [MessageBubbleComponent],
  template: `
    <div #container class="messages">
      @if (messages().length === 0) {
        <div class="welcome-message">
          <div class="welcome-icon">🌱</div>
          <h2>Bienvenido a AgroCanarias IA</h2>
          <p>Tu asistente técnico agrícola de confianza</p>
          <div class="quick-topics">
            <span>💧 Riego y fertilización</span>
            <span>🧪 Fitosanitarios</span>
            <span>📋 Cuaderno de campo</span>
            <span>🏛️ Ayudas y subvenciones</span>
          </div>
        </div>
      }
      @for (m of messages(); track $index) {
        <app-message-bubble [msg]="m" />
      }
      @if (loading()) {
        <div class="message bot">
          <div class="avatar">🌿</div>
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
      min-height: 0;
    }
    .welcome-message {
      text-align: center;
      padding: 3rem 1rem;
      color: #2d3436;
    }
    .welcome-icon {
      font-size: 4rem;
      margin-bottom: 1rem;
    }
    .welcome-message h2 {
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
      color: #2d5a3d;
    }
    .welcome-message p {
      color: #636e72;
      margin-bottom: 1.5rem;
    }
    .quick-topics {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      justify-content: center;
    }
    .quick-topics span {
      background: white;
      padding: 0.5rem 1rem;
      border-radius: 20px;
      font-size: 0.85rem;
      color: #2d5a3d;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .message { display: flex; align-items: flex-start; gap: 0.75rem; max-width: 80%; }
    .bot { align-self: flex-start; }
    .avatar {
      width: 40px; height: 40px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.2rem; flex-shrink: 0;
      background: linear-gradient(135deg, #00b894 0%, #55efc4 100%);
    }
    .bubble {
      padding: 0.9rem 1.1rem; border-radius: 18px; line-height: 1.5;
      background: white; color: #2d3436; border-bottom-left-radius: 4px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .bubble.loading {
      display: flex; gap: 4px; align-items: center;
    }
    .dot {
      width: 8px; height: 8px; background: #00b894;
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
export class MessageListComponent implements OnDestroy {
  messages = input.required<Message[]>();
  loading = input.required<boolean>();

  container = viewChild<ElementRef<HTMLDivElement>>('container');

  private scrollTimer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    effect(() => {
      this.messages();
      if (this.scrollTimer !== null) {
        clearTimeout(this.scrollTimer);
      }
      this.scrollTimer = setTimeout(() => {
        this.scrollToBottom();
        this.scrollTimer = null;
      }, 50);
    });
  }

  ngOnDestroy(): void {
    if (this.scrollTimer !== null) {
      clearTimeout(this.scrollTimer);
      this.scrollTimer = null;
    }
  }

  private scrollToBottom(): void {
    const el = this.container();
    if (el) el.nativeElement.scrollTop = el.nativeElement.scrollHeight;
  }
}
