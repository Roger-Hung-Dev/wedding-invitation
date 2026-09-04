# 參考：測試範例

## api service（HttpTestingController）

```ts
// src/app/api/task.api.spec.ts
import { provideHttpClient } from '@angular/common/http'
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing'
import { TestBed } from '@angular/core/testing'
import { TaskApiService } from './task.api'
import { env } from '../core/config/env'

describe('TaskApiService', () => {
  let service: TaskApiService
  let httpMock: HttpTestingController

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    })
    service = TestBed.inject(TaskApiService)
    httpMock = TestBed.inject(HttpTestingController)
  })

  // 抓出「測完還有沒被消化的請求」
  afterEach(() => httpMock.verify())

  it('getAll 應對正確的 URL 發 GET', () => {
    const expected = [{ id: '1', title: '測試任務' }]
    let actual: unknown

    service.getAll().subscribe((tasks) => (actual = tasks))

    const req = httpMock.expectOne(`${env.apiBaseUrl}/tasks`)
    expect(req.request.method).toBe('GET')
    req.flush(expected)

    expect(actual).toEqual(expected)
  })

  it('create 應把 payload 放進 request body', () => {
    const payload = { title: '新任務' }

    service.create(payload).subscribe()

    const req = httpMock.expectOne(`${env.apiBaseUrl}/tasks`)
    expect(req.request.method).toBe('POST')
    expect(req.request.body).toEqual(payload)
    req.flush({ id: '1', ...payload })
  })
})
```

## store（假 api service）

```ts
// src/app/features/task/task.store.spec.ts
import { TestBed } from '@angular/core/testing'
import { of, throwError } from 'rxjs'
import { TaskApiService } from '../../api/task.api'
import { TaskStore } from './task.store'

describe('TaskStore', () => {
  const apiMock = {
    getAll: jest.fn(),
    create: jest.fn(),
    remove: jest.fn(),
  }

  let store: TaskStore

  beforeEach(() => {
    jest.resetAllMocks()
    TestBed.configureTestingModule({
      providers: [{ provide: TaskApiService, useValue: apiMock }],
    })
    store = TestBed.inject(TaskStore)
  })

  it('load 成功後應填入資料並結束 loading', () => {
    const tasks = [{ id: '1', title: '測試任務' }]
    apiMock.getAll.mockReturnValue(of(tasks))

    store.load()

    // signal 同步讀取，不需要 tick()
    expect(store.tasks()).toEqual(tasks)
    expect(store.isLoading()).toBe(false)
    expect(store.error()).toBeNull()
    expect(store.taskCount()).toBe(1)
  })

  it('load 失敗後應記錄錯誤並結束 loading', () => {
    const apiError = { code: 'SERVER_ERROR', message: '系統忙碌' }
    apiMock.getAll.mockReturnValue(throwError(() => apiError))

    store.load()

    expect(store.error()).toEqual(apiError)
    expect(store.isLoading()).toBe(false)
    expect(store.hasError()).toBe(true)
  })

  it('remove 成功後應從清單移除該筆', () => {
    apiMock.getAll.mockReturnValue(of([{ id: '1', title: 'A' }, { id: '2', title: 'B' }]))
    apiMock.remove.mockReturnValue(of(undefined))
    store.load()

    store.remove('1')

    expect(store.tasks().map((t) => t.id)).toEqual(['2'])
  })
})
```

## 元件（假 store）

```ts
// src/app/features/task/task-list.component.spec.ts
import { ComponentFixture, TestBed } from '@angular/core/testing'
import { signal } from '@angular/core'
import { TaskListComponent } from './task-list.component'
import { TaskStore } from './task.store'

describe('TaskListComponent', () => {
  // 假 store：用真的 signal，讓元件的反應性行為與正式環境一致
  const storeMock = {
    tasks: signal([{ id: '1', title: '測試任務' }]),
    isLoading: signal(false),
    error: signal(null),
    load: jest.fn(),
  }

  let fixture: ComponentFixture<TaskListComponent>

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TaskListComponent], // standalone 元件放 imports
      providers: [{ provide: TaskStore, useValue: storeMock }],
    }).compileComponents()

    fixture = TestBed.createComponent(TaskListComponent)
    fixture.detectChanges() // 觸發 ngOnInit
  })

  it('初始化時應呼叫 store.load()', () => {
    expect(storeMock.load).toHaveBeenCalled()
  })

  it('載入中時應顯示載入提示', () => {
    storeMock.isLoading.set(true)
    fixture.detectChanges()

    expect(fixture.nativeElement.textContent).toContain('載入中')
  })
})
```

> 假 store 用**真的 signal**（而非 `jest.fn()` 回傳值）是刻意的：這樣 `.set()` 就能驅動元件重繪，測出來的行為跟正式環境一致。
