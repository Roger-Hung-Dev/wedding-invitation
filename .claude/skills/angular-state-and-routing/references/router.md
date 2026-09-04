# 參考：路由設定

## 路由表

```ts
// src/app/app.routes.ts
import type { Routes } from '@angular/router'
import { authGuard } from './core/guards/auth.guard'

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'tasks' },
  {
    path: 'tasks',
    title: '任務列表',
    loadComponent: () => import('./features/task/task-list.component').then((m) => m.TaskListComponent),
  },
  {
    path: 'tasks/:id',
    title: '任務明細',
    canActivate: [authGuard],
    loadComponent: () => import('./features/task/task-detail.component').then((m) => m.TaskDetailComponent),
  },
  {
    path: '**',
    loadComponent: () => import('./shared/not-found.component').then((m) => m.NotFoundComponent),
  },
]
```

- **一律 lazy load**（`loadComponent`），不要靜態 import 頁面元件。
- `title` 直接設在路由上，Angular 會自動更新瀏覽器標題。
- `path: '**'` 一定放**最後**（比對是由上而下，放前面會吃掉所有路由）。

## 路由參數綁進 input()

`app.config.ts` 有 `provideRouter(routes, withComponentInputBinding())` 時，路由參數／query／resolve 資料會自動綁到**同名的 `input()`**，不必注入 `ActivatedRoute`：

```ts
// src/app/features/task/task-detail.component.ts
@Component({
  selector: 'app-task-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<h1>{{ store.current()?.title }}</h1>`,
})
export class TaskDetailComponent {
  protected readonly store = inject(TaskStore)

  // 對應路由的 :id —— 名稱必須一致
  readonly id = input.required<string>()

  constructor() {
    // 路由參數變動時重新載入（同一元件實例被重用的情況）
    effect(() => this.store.loadById(this.id()))
  }
}
```

> 這是 `effect()` 的**正當用途**：把 signal 變動接到一個副作用（觸發載入），不是拿來同步狀態。

## 導頁

```ts
private readonly router = inject(Router)

goToDetail(id: string): void {
  this.router.navigate(['/tasks', id])
}
```

樣板則用 `routerLink`：

```html
<a [routerLink]="['/tasks', task.id]">{{ task.title }}</a>
```

- 路徑字串集中在 `app.routes.ts`，不要散落在各元件；需要跨處共用時抽成常數。
- 別忘了在元件的 `imports: [RouterLink]` 加入指令，否則 `routerLink` 不會生效（`strictTemplates` 下會直接報錯，是好事）。
