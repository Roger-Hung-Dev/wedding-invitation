import { Injectable, inject } from '@angular/core'
import { NotifyService } from '../core/notify.service'
import { ToastService } from './toast.service'

@Injectable({ providedIn: 'root' })
export class BootstrapNotifyService extends NotifyService {
  private readonly toast = inject(ToastService)

  override error(message: string): void {
    this.toast.push({ message, variant: 'danger' })
  }

  override success(message: string): void {
    this.toast.push({ message, variant: 'success' })
  }
}
