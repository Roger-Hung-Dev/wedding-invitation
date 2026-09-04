import { ChangeDetectionStrategy, Component, inject } from '@angular/core'
import { ToastService } from './toast.service'

/**
 * 全站唯一的 toast 渲染出口。本站目前沒有需要觸發提示的互動（無表單送出、無 API），
 * 掛在根元件是為了讓 NotifyService 這條可插拔鏈路完整可用，供未來擴充。
 */
@Component({
  selector: 'app-toast-container',
  imports: [],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 1080">
      @for (toast of toastService.messages(); track toast.id) {
        <div class="toast show align-items-center border-0" [class.text-bg-danger]="toast.variant === 'danger'" [class.text-bg-success]="toast.variant === 'success'">
          <div class="d-flex">
            <div class="toast-body">{{ toast.message }}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" (click)="toastService.dismiss(toast.id)"></button>
          </div>
        </div>
      }
    </div>
  `,
})
export class ToastContainerComponent {
  protected readonly toastService = inject(ToastService)
}
