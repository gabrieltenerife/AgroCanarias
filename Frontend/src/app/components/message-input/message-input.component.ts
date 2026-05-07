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
        placeholder="Escribe tu mensaje sobre agricultura..."
        [disabled]="disabled()"
      />
      <button (click)="onSend()" [disabled]="disabled()">➤</button>
    </div>
  `,
  styles: [`
    .input-container {
      display: flex; gap: 0.75rem; padding: 1rem 1.5rem;
      background: white; border-top: 1px solid #d4e6d4;
    }
    input {
      flex: 1; padding: 0.8rem 1.2rem;
      border: 2px solid #d4e6d4; border-radius: 25px;
      font-size: 1rem; outline: none;
      transition: border-color 0.3s ease;
    }
    input:focus { border-color: #4a7c59; }
    input:disabled { background: #e8f5e9; cursor: not-allowed; }
    button {
      width: 48px; height: 48px; border: none; border-radius: 50%;
      background: #4a7c59; color: white; font-size: 1.2rem;
      cursor: pointer; transition: all 0.3s ease;
      display: flex; align-items: center; justify-content: center;
    }
    button:hover:not(:disabled) { background: #2d5a3d; transform: scale(1.1); }
    button:disabled { background: #8fbc8f; cursor: not-allowed; }
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