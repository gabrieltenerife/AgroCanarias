import { Component, output } from '@angular/core';

@Component({
  selector: 'app-chat-header',
  standalone: true,
  template: `
    <header class="header">
      <div class="logo">
        <span class="icon">🌿</span>
        <h1>AgroCanarias IA</h1>
      </div>
      <button class="new-chat-btn" (click)="newChat.emit()">Nueva Conversación</button>
    </header>
  `,
  styles: [`
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 1.5rem;
      background: #4a7c59;
      color: white;
    }
    .logo { display: flex; align-items: center; gap: 0.5rem; }
    .logo h1 { font-size: 1.5rem; font-weight: 600; margin: 0; }
    .icon { font-size: 1.8rem; }
    .new-chat-btn {
      padding: 0.6rem 1.2rem;
      background: #8fbc8f;
      border: none;
      border-radius: 20px;
      color: #2d5a3d;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s ease;
    }
    .new-chat-btn:hover { background: white; transform: scale(1.05); }
  `]
})
export class ChatHeaderComponent {
  newChat = output<void>();
}