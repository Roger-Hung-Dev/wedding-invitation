import { ChangeDetectionStrategy, Component } from '@angular/core'
import { RouterOutlet } from '@angular/router'
import { IntroGateComponent } from './features/intro-gate/intro-gate.component'
import { ToastContainerComponent } from './shared/toast-container.component'

/**
 * 應用外殼。喜帖本體在 HomeComponent，由路由依宴席版本載入。
 *
 * 開場層與訊息容器留在外殼、不進 router-outlet：兩個版本共用同一個開場，
 * 放進去會在切換版本時被重建，開場層就會再蓋一次。
 */
@Component({
  selector: 'app-root',
  imports: [RouterOutlet, IntroGateComponent, ToastContainerComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {}
