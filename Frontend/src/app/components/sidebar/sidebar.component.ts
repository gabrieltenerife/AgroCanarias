import { Component, input, output } from '@angular/core';

export interface Conversation {
  thread_id: string;
  title: string;
  preview: string;
  message_count: number;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  template: `
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <span class="logo-icon">🌿</span>
          <span class="logo-text">AgroCanarias</span>
        </div>
        <button class="new-chat-btn" (click)="newChat.emit()">
          <span class="plus-icon">+</span>
          Nueva
        </button>
      </div>
      
      <div class="conversations-list">
        @for (conv of conversations(); track conv.thread_id) {
          <div 
            class="conversation-item" 
            [class.active]="activeThreadId() === conv.thread_id"
            (click)="selectConversation.emit(conv.thread_id)"
          >
            <div class="conv-icon">🌱</div>
            <div class="conv-info">
              <div class="conv-title">{{ conv.title }}</div>
              <div class="conv-preview">{{ conv.preview }}</div>
            </div>
            <button 
              class="delete-btn" 
              (click)="onDelete($event, conv.thread_id)"
              title="Eliminar"
            >×</button>
          </div>
        }
        
        @if (conversations().length === 0) {
          <div class="empty-state">
            <span class="empty-icon">📭</span>
            <p>No hay conversaciones</p>
          </div>
        }
      </div>
      
      <div class="sidebar-footer">
        <div class="footer-text">AgroCanarias IA v1.0</div>
      </div>
    </aside>
  `,
  styles: [`
    .sidebar {
      width: 280px;
      height: 100vh;
      background: linear-gradient(180deg, #2d3436 0%, #1e272e 100%);
      display: flex;
      flex-direction: column;
      border-right: 1px solid rgba(255,255,255,0.08);
    }
    
    .sidebar-header {
      padding: 1.25rem;
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    
    .logo {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }
    
    .logo-icon {
      font-size: 1.5rem;
    }
    
    .logo-text {
      font-size: 1.1rem;
      font-weight: 600;
      color: #ecf0f1;
      letter-spacing: 0.5px;
    }
    
    .new-chat-btn {
      width: 100%;
      padding: 0.75rem 1rem;
      background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
      border: none;
      border-radius: 10px;
      color: white;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      transition: all 0.2s ease;
    }
    
    .new-chat-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0,184,148,0.3);
    }
    
    .plus-icon {
      font-size: 1.2rem;
      font-weight: bold;
    }
    
    .conversations-list {
      flex: 1;
      overflow-y: auto;
      padding: 0.75rem;
    }
    
    .conversation-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.85rem;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.15s ease;
      margin-bottom: 0.5rem;
      position: relative;
    }
    
    .conversation-item:hover {
      background: rgba(255,255,255,0.06);
    }
    
    .conversation-item.active {
      background: linear-gradient(135deg, rgba(0,184,148,0.2) 0%, rgba(0,160,133,0.15) 100%);
      border: 1px solid rgba(0,184,148,0.3);
    }
    
    .conv-icon {
      width: 36px;
      height: 36px;
      border-radius: 8px;
      background: linear-gradient(135deg, #00b894 0%, #55efc4 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1rem;
      flex-shrink: 0;
    }
    
    .conv-info {
      flex: 1;
      min-width: 0;
    }
    
    .conv-title {
      font-size: 0.9rem;
      font-weight: 500;
      color: #ecf0f1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    
    .conv-preview {
      font-size: 0.75rem;
      color: #a0a0a0;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-top: 2px;
    }
    
    .delete-btn {
      position: absolute;
      right: 8px;
      top: 50%;
      transform: translateY(-50%);
      width: 22px;
      height: 22px;
      border: none;
      background: rgba(231,76,60,0.8);
      color: white;
      border-radius: 50%;
      font-size: 1rem;
      cursor: pointer;
      opacity: 0;
      transition: opacity 0.15s ease;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .conversation-item:hover .delete-btn {
      opacity: 1;
    }
    
    .delete-btn:hover {
      background: #e74c3c;
    }
    
    .empty-state {
      text-align: center;
      padding: 2rem;
      color: #636e72;
    }
    
    .empty-icon {
      font-size: 2.5rem;
      display: block;
      margin-bottom: 0.5rem;
    }
    
    .sidebar-footer {
      padding: 1rem;
      border-top: 1px solid rgba(255,255,255,0.08);
      text-align: center;
    }
    
    .footer-text {
      font-size: 0.7rem;
      color: #636e72;
    }
  `]
})
export class SidebarComponent {
  conversations = input.required<Conversation[]>();
  activeThreadId = input.required<string | null>();
  
  selectConversation = output<string>();
  newChat = output<void>();
  deleteConversation = output<string>();
  
  onDelete(event: Event, threadId: string): void {
    event.stopPropagation();
    if (window.confirm('¿Eliminar esta conversación?')) {
      this.deleteConversation.emit(threadId);
    }
  }
}