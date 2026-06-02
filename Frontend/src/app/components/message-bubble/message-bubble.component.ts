import { Component, computed, input, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';
import { Message } from '../../models/message.model';

marked.setOptions({
  breaks: true,
  gfm: true,
});

@Component({
  selector: 'app-message-bubble',
  standalone: true,
  template: `
    <div class="message" [class.user]="msg().type === 'user'" [class.bot]="msg().type === 'bot'">
      <div class="avatar">
        @if (msg().type === 'user') { 👤 } @else { 🌱 }
      </div>
      <div class="bubble" [innerHTML]="rendered()"></div>
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
      padding: 0.8rem 1rem; border-radius: 15px; line-height: 1.5;
      word-wrap: break-word; overflow-wrap: break-word;
    }
    .user .bubble {
      background: #4a7c59; color: white; border-bottom-right-radius: 4px;
    }
    .bot .bubble {
      background: white; color: #2d5a3d; border: 1px solid #8fbc8f; border-bottom-left-radius: 4px;
    }
    .bubble :first-child { margin-top: 0; }
    .bubble :last-child { margin-bottom: 0; }
    .bubble p { margin: 0 0 0.5rem 0; white-space: pre-wrap; }
    .bubble ul, .bubble ol { margin: 0.25rem 0 0.5rem 1.25rem; padding: 0; }
    .bubble li { margin-bottom: 0.25rem; }
    .bubble code {
      background: rgba(0,0,0,0.08); padding: 0.1rem 0.35rem;
      border-radius: 4px; font-family: monospace; font-size: 0.9em;
    }
    .bubble pre {
      background: rgba(0,0,0,0.06); padding: 0.6rem 0.8rem;
      border-radius: 8px; overflow-x: auto; margin: 0.5rem 0;
    }
    .bubble pre code { background: transparent; padding: 0; }
    .bubble strong { font-weight: 700; }
    .bubble em { font-style: italic; }
    .bubble a { color: #00a085; text-decoration: underline; }
    .user .bubble a { color: #dfe6e9; }
    .bubble h1, .bubble h2, .bubble h3 {
      margin: 0.5rem 0 0.4rem 0; font-weight: 700; line-height: 1.25;
    }
    .bubble h1 { font-size: 1.15rem; }
    .bubble h2 { font-size: 1.05rem; }
    .bubble h3 { font-size: 0.95rem; }
    .bubble blockquote {
      border-left: 3px solid #8fbc8f; padding-left: 0.75rem;
      margin: 0.4rem 0; color: #4a4a4a;
    }
  `]
})
export class MessageBubbleComponent {
  private sanitizer = inject(DomSanitizer);
  msg = input.required<Message>();

  rendered = computed<SafeHtml>(() => {
    const content = this.msg().content || '';
    if (this.msg().type === 'user') {
      return this.sanitizer.bypassSecurityTrustHtml(this.escapeAndPreserveNewlines(content));
    }
    const html = marked.parse(content, { async: false }) as string;
    return this.sanitizer.bypassSecurityTrustHtml(html);
  });

  private escapeAndPreserveNewlines(text: string): string {
    const escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    return escaped.replace(/\n/g, '<br>');
  }
}
