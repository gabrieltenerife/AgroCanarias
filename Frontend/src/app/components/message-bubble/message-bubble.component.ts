import { Component, input } from '@angular/core';
import { Message } from '../../models/message.model';

@Component({
  selector: 'app-message-bubble',
  standalone: true,
  template: `
    <div class="message" [class.user]="msg().type === 'user'" [class.bot]="msg().type === 'bot'">
      <div class="avatar">
        @if (msg().type === 'user') { 👤 } @else { 🌱 }
      </div>
      <div class="bubble">{{ msg().content }}</div>
    </div>
  `,
  styles: [`
    .message { display: flex; align-items: flex-start; gap: 0.75rem; max-width: 80%; }
    .user { align-self: flex-end; flex-direction: row-reverse; }
    .avatar {
      width: 40px; height: 40px;
      border-radius: 50%;
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
  `]
})
export class MessageBubbleComponent {
  msg = input.required<Message>();
}