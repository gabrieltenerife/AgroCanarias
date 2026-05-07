import { Component, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-message-input',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="input-container">
      <input 
        type="text" 
        [ngModel]="text()" 
        (ngModelChange)="text.set($event)"
        (keyup.enter)="onSend()"
        placeholder="¿En qué puedo ayudarte hoy?"
        [disabled]="disabled()"
      />
      <button (click)="onSend()" [disabled]="disabled()">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
        </svg>
      </button>
    </div>
  `,
  styles: [`
    .input-container {
      display: flex; gap: 0.75rem; padding: 1rem 1.5rem;
      background: white; border-top: 1px solid rgba(0,0,0,0.05);
      box-shadow: 0 -2px 10px rgba(0,0,0,0.03);
      flex-shrink: 0;
      min-height: 70px;
      align-items: center;
    }
    input {
      flex: 1; padding: 0.9rem 1.2rem;
      border: 2px solid #dfe6e9; border-radius: 25px;
      font-size: 0.95rem; outline: none;
      transition: all 0.3s ease;
      background: #f8f9fa;
    }
    input:focus { 
      border-color: #00b894; 
      background: white;
      box-shadow: 0 0 0 3px rgba(0,184,148,0.1);
    }
    input:disabled { background: #f8f9fa; cursor: not-allowed; }
    button {
      width: 48px; height: 48px; border: none; border-radius: 50%;
      background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
      color: white;
      cursor: pointer; transition: all 0.3s ease;
      display: flex; align-items: center; justify-content: center;
    }
    button:hover:not(:disabled) { 
      transform: scale(1.05);
      box-shadow: 0 4px 15px rgba(0,184,148,0.4);
    }
    button:disabled { 
      background: #b2bec3; cursor: not-allowed; 
    }
  `]
})
export class MessageInputComponent {
  text = signal('');
  disabled = input<boolean>(false);
  send = output<string>();

  onSend(): void {
    const value = this.text().trim();
    if (value) {
      this.send.emit(value);
      this.text.set('');
    }
  }
}