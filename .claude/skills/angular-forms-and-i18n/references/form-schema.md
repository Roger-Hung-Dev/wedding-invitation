# 參考：表單驗證規則

## 預設：Angular 內建 Validators

```ts
// src/app/features/task/task-form.component.ts（節錄）
import { NonNullableFormBuilder, Validators } from '@angular/forms'

private readonly fb = inject(NonNullableFormBuilder)

protected readonly form = this.fb.group({
  title: ['', [Validators.required, Validators.maxLength(50)]],
  dueDate: [''],
})
```

> 用 `NonNullableFormBuilder` 而非 `FormBuilder`：控制項型別不會混進 `null`，`reset()` 也回到初始值而非 null。

## 升級為 Zod 的時機

符合下列情況才升級：

1. 該資料模型需**跨層共用型別**（表單輸入 ≈ API payload / 回應）；
2. 驗證**複雜**（跨欄位、條件式、動態規則）。

## schema 是單一真相來源

型別一律由 `z.infer` 導出，**不要另外手寫一份 `interface`** —— 兩份遲早走鐘。

```ts
// src/app/schemas/task.schema.ts
import { z } from 'zod'

export const taskSchema = z.object({
  title: z.string().min(1, 'task.errors.titleRequired').max(50, 'task.errors.titleTooLong'),
  dueDate: z.string().optional(),
})

// 表單輸入型別
export type TaskInput = z.infer<typeof taskSchema>

// API 回傳的完整實體
export interface Task extends TaskInput {
  readonly id: string
}
```

上面 schema 裡填的是 **i18n key**，不是中文字串 —— 顯示前才翻譯（見 [i18n-setup.md](i18n-setup.md)）。

## zodValidator adapter

把 Zod schema 接進 Reactive Forms 的共用 adapter，**只寫一份**放 `core/validators/`：

```ts
// src/app/core/validators/zod.validator.ts
import type { ValidatorFn } from '@angular/forms'
import type { ZodType } from 'zod'

/** 單一欄位：把 Zod schema 包成 Angular ValidatorFn */
export function zodValidator(schema: ZodType): ValidatorFn {
  return (control) => {
    const result = schema.safeParse(control.value)
    if (result.success) return null
    // 回傳的 message 是 i18n key，由樣板端翻譯
    return { zod: result.error.issues[0]?.message ?? 'common.errors.invalid' }
  }
}
```

```ts
// 使用：schema 與表單共用同一份規則
import { taskSchema } from '../../schemas/task.schema'
import { zodValidator } from '../../core/validators/zod.validator'

protected readonly form = this.fb.group({
  title: ['', [zodValidator(taskSchema.shape.title)]],
  dueDate: [''],
})
```

## 跨欄位驗證

這正是「該升級為 Zod」的典型場景 —— 內建 `Validators` 只能驗單一欄位。跨欄位的 schema 掛在 **FormGroup 層級**：

```ts
// schema
export const dateRangeSchema = z
  .object({ startDate: z.string(), endDate: z.string() })
  .refine((v) => v.startDate <= v.endDate, {
    message: 'common.errors.endBeforeStart',
    path: ['endDate'], // 錯誤掛在 endDate 上，UI 才知道要標紅哪一欄
  })
```

```ts
// src/app/core/validators/zod.validator.ts（追加；import 補上 FormGroup）
import type { FormGroup, ValidatorFn } from '@angular/forms'

/** 整組：把 Zod object schema 包成 FormGroup 層級的 ValidatorFn，錯誤依 path 分派到各欄位 */
export function zodGroupValidator(schema: ZodType): ValidatorFn {
  return (group) => {
    const result = schema.safeParse(group.value)
    if (result.success) return null

    for (const issue of result.error.issues) {
      const key = issue.path[0]
      if (typeof key !== 'string') continue
      const control = (group as FormGroup).get(key)
      // 保留既有錯誤，只補上 zod 這一項
      control?.setErrors({ ...control.errors, zod: issue.message })
    }
    return { zod: true }
  }
}
```

```ts
protected readonly form = this.fb.group(
  { startDate: [''], endDate: [''] },
  { validators: [zodGroupValidator(dateRangeSchema)] },
)
```

> `path` 一定要填，否則錯誤會掛在 group 層級，欄位錯誤顯示接不到。

## 跨層共用

當表單輸入 ≈ API payload 時，型別來自同一份 schema，讓表單與 `api/` 共用：

```ts
// src/app/api/task.api.ts
import type { Task, TaskInput } from '../schemas/task.schema'

create(payload: TaskInput): Observable<Task> {
  return this.http.post<Task>(this.baseUrl, payload)
}
```

## 接到 UI

「驗證結果怎麼顯示」是 UI 元件庫的事：

- `ui-angular-material` → `mat-form-field` + `mat-error`。
- `ui-bootstrap5` → `.is-invalid` / `.invalid-feedback`。

見對應 `ui-*` skill 的 `references/forms-validation.md`。
