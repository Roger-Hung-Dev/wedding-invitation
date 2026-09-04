import { Injectable, signal } from '@angular/core'

export interface ToastMessage {
  readonly id: number
  readonly message: string
  readonly variant: 'danger' | 'success'
}

@Injectable({ providedIn: 'root' })
export class ToastService {
  private readonly _messages = signal<ToastMessage[]>([])
  readonly messages = this._messages.asReadonly()

  private nextId = 0

  push(toast: Omit<ToastMessage, 'id'>): void {
    const id = this.nextId++
    this._messages.update((list) => [...list, { ...toast, id }])
    setTimeout(() => this.dismiss(id), 4000)
  }

  dismiss(id: number): void {
    this._messages.update((list) => list.filter((m) => m.id !== id))
  }
}
