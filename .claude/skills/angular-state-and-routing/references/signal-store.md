# 參考：Signals + Service store

一個 feature 一個 store。它是 **facade**：對元件隱藏 `api/` 細節，只暴露唯讀 signal 與動作。

```ts
// src/app/features/task/task.store.ts
import { Injectable, computed, inject, signal } from '@angular/core'
import { TaskApiService } from '../../api/task.api'
import type { ApiError } from '../../core/types/api'
import type { Task, TaskInput } from '../../schemas/task.schema'

@Injectable({ providedIn: 'root' })
export class TaskStore {
  private readonly api = inject(TaskApiService)

  // ── 內部可寫狀態（private）
  private readonly _tasks = signal<readonly Task[]>([])
  private readonly _isLoading = signal(false)
  private readonly _error = signal<ApiError | null>(null)

  // ── 對外唯讀
  readonly tasks = this._tasks.asReadonly()
  readonly isLoading = this._isLoading.asReadonly()
  readonly error = this._error.asReadonly()

  // ── 衍生值一律 computed，不要用 effect 去寫 signal
  readonly taskCount = computed(() => this._tasks().length)
  readonly hasError = computed(() => this._error() !== null)

  // ── 動作
  load(): void {
    this._isLoading.set(true)
    this._error.set(null)

    this.api.getAll().subscribe({
      next: (tasks) => {
        this._tasks.set(tasks)
        this._isLoading.set(false)
      },
      error: (error: ApiError) => {
        this._error.set(error)
        this._isLoading.set(false)
      },
    })
  }

  create(payload: TaskInput): void {
    this.api.create(payload).subscribe({
      // update 而非 set：以現有值為基礎推導，避免競態
      next: (created) => this._tasks.update((tasks) => [...tasks, created]),
      error: (error: ApiError) => this._error.set(error),
    })
  }

  remove(id: string): void {
    this.api.remove(id).subscribe({
      next: () => this._tasks.update((tasks) => tasks.filter((t) => t.id !== id)),
      error: (error: ApiError) => this._error.set(error),
    })
  }
}
```

## 元件端

元件只注入 store、只讀 signal、只呼叫動作：

```ts
// src/app/features/task/task-list.component.ts
import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core'
import { TaskStore } from './task.store'

@Component({
  selector: 'app-task-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <!-- 載入中 / 錯誤 / 資料 三態，各自用專案 UI 元件庫的對應元件呈現（見 ui-* skill） -->
    @if (store.isLoading()) {
      <p>載入中…</p>
    } @else if (store.error(); as error) {
      <p role="alert">{{ error.message }}</p>
    } @else {
      <ul>
        @for (task of store.tasks(); track task.id) {
          <li>{{ task.title }}</li>
        } @empty {
          <li>目前沒有項目</li>
        }
      </ul>
    }
  `,
})
export class TaskListComponent implements OnInit {
  // 樣板要讀，所以是 protected/public（不是 private）
  protected readonly store = inject(TaskStore)

  ngOnInit(): void {
    this.store.load()
  }
}
```

> 上面刻意用原生元素，是為了凸顯 **store 的三態資料流**；實際切版時換成專案 UI 元件庫的骨架屏 / 警示 / 清單元件（`ui-angular-material` → `mat-progress-spinner`／`mat-error`／`mat-list`；`ui-bootstrap5` → `.placeholder-glow`／`.alert`／`.list-group`）。三態的**結構**不變，變的只是元件。

## 鐵律

- **`@for` 的 `track` 填穩定唯一值**（通常是 `id`），不要填 `$index` —— 會讓 DOM 重用失效、輸入焦點跳掉。
- **`update()` 優於 `set()`**：以現有值推導新值時用 `update`，避免讀-改-寫的競態。
- **state 用 `readonly` 陣列**（`readonly Task[]`）並以展開產生新陣列，不要 `push` 原陣列 —— signal 靠參考變更觸發。
- **不要在 store 裡注入 UI 元件庫**：提示是攔截器（系統性錯誤）或元件（業務錯誤）的事。
