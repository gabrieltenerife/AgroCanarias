import { Component, inject, OnInit } from '@angular/core';
import { ChatService } from './services/chat.service';
import { SidebarComponent } from './components/sidebar/sidebar.component';
import { MessageListComponent } from './components/message-list/message-list.component';
import { MessageInputComponent } from './components/message-input/message-input.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [SidebarComponent, MessageListComponent, MessageInputComponent],
  template: `
    <div class="app-container">
      <app-sidebar 
        [conversations]="chat.conversations()"
        [activeThreadId]="chat.threadId()"
        (selectConversation)="onSelectConversation($event)"
        (newChat)="onNewChat()"
        (deleteConversation)="chat.deleteConversation($event)"
      />
      <main class="chat-area">
        <header class="chat-header">
          <div class="header-content">
            <span class="header-icon">🌿</span>
            <h1>AgroCanarias IA</h1>
          </div>
        </header>
        <app-message-list [messages]="chat.messages()" [loading]="chat.isLoading()" />
        <app-message-input (send)="chat.sendMessage($event)" [disabled]="chat.isLoading()" />
      </main>
    </div>
  `,
  styles: [`
    .app-container {
      display: flex;
      height: 100vh;
      background: linear-gradient(135deg, #1e272e 0%, #2d3436 100%);
    }
    .chat-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      background: linear-gradient(180deg, #dfe6e9 0%, #c8d6e5 100%);
    }
    .chat-header {
      padding: 1rem 1.5rem;
      background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
      color: white;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .header-content {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .header-icon {
      font-size: 1.5rem;
    }
    .chat-header h1 {
      margin: 0;
      font-size: 1.25rem;
      font-weight: 600;
    }
    app-message-list {
      flex: 1;
      min-height: 0;
      display: flex;
      flex-direction: column;
    }
    app-message-input {
      flex-shrink: 0;
    }
  `]
})
export class App implements OnInit {
  chat = inject(ChatService);

  async ngOnInit() {
    await this.chat.loadConversations();
    if (this.chat.conversations().length > 0) {
      await this.chat.selectConversation(this.chat.conversations()[0].thread_id);
    } else {
      await this.chat.newChat();
    }
  }

  async onSelectConversation(threadId: string) {
    await this.chat.selectConversation(threadId);
  }

  async onNewChat() {
    await this.chat.newChat();
  }
}