import { Component, inject, OnInit } from '@angular/core';
import { ChatService } from './services/chat.service';
import { ChatHeaderComponent } from './components/chat-header/chat-header.component';
import { MessageListComponent } from './components/message-list/message-list.component';
import { MessageInputComponent } from './components/message-input/message-input.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ChatHeaderComponent, MessageListComponent, MessageInputComponent],
  template: `
    <div class="container">
      <app-chat-header (newChat)="chat.newChat()" />
      <app-message-list [messages]="chat.messages()" [loading]="chat.isLoading()" />
      <app-message-input (send)="chat.sendMessage($event)" [disabled]="chat.isLoading()" />
    </div>
  `,
  styles: [`
    .container {
      max-width: 900px; margin: 0 auto; height: 100vh;
      display: flex; flex-direction: column;
      background: #e8f5e9;
    }
  `]
})
export class App implements OnInit {
  chat = inject(ChatService);

  ngOnInit() {
    this.chat.loadHistory();
  }
}