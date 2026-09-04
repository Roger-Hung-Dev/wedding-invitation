# 參考：精簡分層的一個 feature 從頭到尾

> 目的是完整呈現相依鏈：`component → store → api → core`。各層的深入規範見對應 skill（`angular-api-integration`、`angular-state-and-routing`、`angular-forms-and-i18n`）。

## 1. `schemas/task.schema.ts` —— 型別與規則

```ts
import { z } from 'zod'

export const taskSchema = z.object({
  id: z.string(),
  title: z.string().min(1).max(120),
  status: z.enum(['todo', 'doing', 'done']),
  createdAt: z.coerce.date(),
})

export type Task = z.infer<typeof taskSchema>

// 單一實體的判斷寫成純函式，不是 class 方法
export function canEdit(task: Task): boolean {
  return task.status !== 'done'
}
```

## 2. `api/task.api.ts` —— 資料存取層

只定義端點、回傳 Observable。不碰狀態、不碰 UI、不做提示。

```ts
import { Injectable, inject } from '@angular/core'
import { HttpClient } from '@angular/common/http'
import { Observable } from 'rxjs'
import { environment } from '../../environments/environment'
import type { Task } from '../schemas/task.schema'

@Injectable({ providedIn: 'root' })
export class TaskApiService {
  private readonly http = inject(HttpClient)
  private readonly baseUrl = `${environment.apiBaseUrl}/tasks`

  getTasks(): Observable<Task[]> {
    return this.http.get<Task[]>(this.baseUrl)
  }

  getTask(id: string): Observable<Task> {
    return this.http.get<Task>(`${this.baseUrl}/${id}`)
  }

  saveTask(task: Task): Observable<Task> {
    return task.id
      ? this.http.put<Task>(`${this.baseUrl}/${task.id}`, task)
      : this.http.post<Task>(this.baseUrl, task)
  }
}
```

## 3. `features/task/task.store.ts` —— 狀態層（兼 Facade）

signal 持狀態、呼叫 api、對外唯讀。

```ts
import { Injectable, computed, inject, signal } from '@angular/core'
import { finalize } from 'rxjs'
import { TaskApiService } from '../../api/task.api'
import { NotifyService } from '../../core/notify.service'
import type { Task } from '../../schemas/task.schema'

@Injectable({ providedIn: 'root' })
export class TaskStore {
  private readonly api = inject(TaskApiService)
  private readonly notify = inject(NotifyService)

  // 內部可寫，對外唯讀
  private readonly _tasks = signal<Task[]>([])
  private readonly _isLoading = signal(false)
  private readonly _error = signal<string | null>(null)

  readonly tasks = this._tasks.asReadonly()
  readonly isLoading = this._isLoading.asReadonly()
  readonly error = this._error.asReadonly()

  // 衍生值一律 computed，不用 effect 去寫 signal
  readonly openTasks = computed(() => this._tasks().filter((t) => t.status !== 'done'))

  loadTasks(): void {
    this._isLoading.set(true)
    this._error.set(null)

    this.api
      .getTasks()
      .pipe(finalize(() => this._isLoading.set(false)))
      .subscribe({
        next: (tasks) => this._tasks.set(tasks),
        error: (err) => this._error.set(err.message),
      })
  }

  saveTask(task: Task): void {
    this._isLoading.set(true)

    this.api
      .saveTask(task)
      .pipe(finalize(() => this._isLoading.set(false)))
      .subscribe({
        next: () => {
          this.notify.success('儲存成功')
          this.loadTasks()
        },
        error: (err) => this._error.set(err.message),
      })
  }
}
```

> `finalize` 是 **RxJS 操作符，放進 `pipe()`** —— 它不是 `subscribe({ ... })` observer 物件的屬性。寫在 observer 裡不會執行，`isLoading` 會永遠卡在 `true`。

## 4. `features/task/task-list.component.ts` —— 表現層

注入 store，不碰 api。

```ts
import { ChangeDetectionStrategy, Component, inject } from '@angular/core'
import { TaskStore } from './task.store'
import type { Task } from '../../schemas/task.schema'

@Component({
  selector: 'app-task-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [/* 見專案的 ui-* skill */],
  template: `
    @if (store.isLoading()) {
      <app-spinner />
    } @else {
      @for (task of store.openTasks(); track task.id) {
        <app-task-card [task]="task" (edit)="onEdit($event)" />
      }
    }

    @if (store.error(); as message) {
      <p class="error">{{ message }}</p>
    }
  `,
})
export class TaskListComponent {
  // store 直接暴露給樣板讀 signal 是刻意的，不必再包一層 getter
  protected readonly store = inject(TaskStore)

  protected onEdit(task: Task): void {
    this.store.saveTask(task)
  }
}
```

## 相依鏈檢查表

做完一個 feature，逐項對一次：

- [ ] 元件有沒有 import 到 `api/` 底下的東西？（不可以）
- [ ] `core/` 或 `api/` 有沒有 import UI 元件庫？（不可以，要提示就注入 `NotifyService`）
- [ ] store 的 signal 對外是不是 `asReadonly()`？
- [ ] 衍生值是不是 `computed()` 而不是 `effect()` 寫 signal？
- [ ] `shared/` 有沒有 import 到 `features/`？（不可以）
- [ ] `finalize` 是不是寫在 `pipe()` 裡而不是 observer 裡？
