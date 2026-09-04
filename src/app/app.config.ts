import { ApplicationConfig, provideBrowserGlobalErrorListeners, provideZonelessChangeDetection } from '@angular/core'
import { NotifyService } from './core/notify.service'
import { BootstrapNotifyService } from './shared/bootstrap-notify.service';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser'

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    // UI 元件庫轉接：換元件庫時只換這一行綁的實作
    { provide: NotifyService, useClass: BootstrapNotifyService }, provideClientHydration(withEventReplay()),
  ],
}
