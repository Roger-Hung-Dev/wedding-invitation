import { ApplicationConfig, provideBrowserGlobalErrorListeners, provideZonelessChangeDetection } from '@angular/core'
import { NotifyService } from './core/notify.service'
import { BootstrapNotifyService } from './shared/bootstrap-notify.service';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser'
import { provideRouter, withComponentInputBinding } from '@angular/router'
import { routes } from './app.routes'

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    // UI 元件庫轉接：換元件庫時只換這一行綁的實作
    { provide: NotifyService, useClass: BootstrapNotifyService },
    provideClientHydration(withEventReplay()),
    // withComponentInputBinding：路由 data 直接綁進元件的 input()，元件不必自己讀 ActivatedRoute
    provideRouter(routes, withComponentInputBinding()),
  ],
}
