# 參考：api 層端點寫法

`api/` 層**只定義端點**：包 `HttpClient`、標好型別、回傳 `Observable<T>`。不碰狀態、不做提示、不 `subscribe`。

```ts
// src/app/api/task.api.ts
import { HttpClient } from '@angular/common/http'
import { Injectable, inject } from '@angular/core'
import type { Observable } from 'rxjs'
import { env } from '../core/config/env'
import type { Task } from '../schemas/task.schema'
import type { TaskInput } from '../schemas/task.schema'

@Injectable({ providedIn: 'root' })
export class TaskApiService {
  private readonly http = inject(HttpClient)
  private readonly baseUrl = `${env.apiBaseUrl}/tasks`

  getAll(): Observable<Task[]> {
    return this.http.get<Task[]>(this.baseUrl)
  }

  getById(id: string): Observable<Task> {
    return this.http.get<Task>(`${this.baseUrl}/${id}`)
  }

  create(payload: TaskInput): Observable<Task> {
    return this.http.post<Task>(this.baseUrl, payload)
  }

  update(id: string, payload: TaskInput): Observable<Task> {
    return this.http.put<Task>(`${this.baseUrl}/${id}`, payload)
  }

  remove(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`)
  }
}
```

## 分頁與查詢參數

用 `HttpParams`，不要自己拼查詢字串（會漏掉編碼）：

```ts
getPaged(page: number, size: number): Observable<Paged<Task>> {
  const params = new HttpParams().set('page', page).set('size', size)
  return this.http.get<Paged<Task>>(this.baseUrl, { params })
}
```

## 鐵律

- **不在 `api/` 裡 `subscribe`** —— 訂閱的時機屬於 store 層。
- **不在 `api/` 裡做提示或導頁** —— 那是攔截器與元件的事。
- **回傳型別一律標註**，且型別來自 `schemas/`（單一真相來源，見 `angular-forms-and-i18n`）。
- **元件不得注入 `TaskApiService`** —— 一律經 `TaskStore`（見 `angular-state-and-routing`）。
