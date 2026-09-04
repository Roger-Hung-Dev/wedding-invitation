# 參考：Bootstrap 5 表單錯誤顯示

Bootstrap 的錯誤顯示靠兩個 class 配合：

- `<input>` 加 `.is-invalid`
- 錯誤訊息放**緊鄰其後**的 `<div class="invalid-feedback">`

CSS 規則是 `.is-invalid ~ .invalid-feedback { display: block }` —— 所以 **`.invalid-feedback` 永遠渲染就好，不用 `v-if` / `@if` 包**，讓 CSS 決定顯不顯示；但**順序不能顛倒**，錯誤訊息必須是 input 的後兄弟元素。

`<form>` 一律加 `novalidate` 關掉瀏覽器原生驗證，錯誤來源只留框架這一套。

> 驗證**規則**怎麼定義見框架 skill（`vue3-forms-and-i18n` / `angular-forms-and-i18n`）；本檔只管**結果怎麼顯示**。

## Vue 3

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { taskSchema, type TaskInput } from '@/schemas/task'

const emit = defineEmits<{ (e: 'save', value: TaskInput): void }>()

const { t } = useI18n()
const form = ref<TaskInput>({ title: '' })
const errors = ref<Partial<Record<keyof TaskInput, string>>>({})

function validate(): boolean {
  const result = taskSchema.safeParse(form.value)
  errors.value = {}
  if (!result.success) {
    for (const issue of result.error.issues) {
      const key = issue.path[0] as keyof TaskInput
      errors.value[key] ??= issue.message // 每欄只顯示第一個錯誤
    }
  }
  return result.success
}

function onSubmit(): void {
  if (validate()) emit('save', form.value)
}
</script>

<template>
  <form novalidate @submit.prevent="onSubmit">
    <div class="mb-3">
      <label class="form-label" for="title">{{ t('task.title') }}</label>
      <input
        id="title"
        v-model="form.title"
        class="form-control"
        :class="{ 'is-invalid': errors.title }"
      />
      <div class="invalid-feedback">{{ errors.title }}</div>
    </div>
    <button class="btn btn-primary" type="submit">{{ t('common.save') }}</button>
  </form>
</template>
```

## Angular（Reactive Forms）

只在欄位被碰過（`dirty` 或 `touched`）之後才顯示錯誤，否則使用者一進畫面就滿江紅。

```ts
import { Component, inject } from '@angular/core'
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms'

@Component({
  selector: 'app-task-form',
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form" novalidate (ngSubmit)="onSubmit()">
      <div class="mb-3">
        <label class="form-label" for="title">標題</label>
        <input
          id="title"
          formControlName="title"
          class="form-control"
          [class.is-invalid]="isInvalid('title')"
        />
        <div class="invalid-feedback">{{ errorOf('title') }}</div>
      </div>
      <button class="btn btn-primary" type="submit">儲存</button>
    </form>
  `,
})
export class TaskFormComponent {
  private readonly fb = inject(NonNullableFormBuilder)

  protected readonly form = this.fb.group({
    title: ['', [Validators.required, Validators.maxLength(50)]],
  })

  protected isInvalid(name: string): boolean {
    const control = this.form.get(name)
    return !!control && control.invalid && (control.dirty || control.touched)
  }

  protected errorOf(name: string): string {
    const errors = this.form.get(name)?.errors
    if (!errors) return ''
    if (errors['required']) return '此欄為必填'
    if (errors['maxlength']) return `最多 ${errors['maxlength'].requiredLength} 字`
    return '格式不正確'
  }

  protected onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched() // 讓未碰過的欄位也顯示錯誤
      return
    }
    // ...送出
  }
}
```

> 上面的 `errorOf` 把訊息寫死只是為了示意。實際專案文案一律走 i18n（見框架 skill），並把這段對照抽成共用的錯誤訊息 mapper，不要每個表單各寫一份。

## 不要做的事

- ❌ 用 `.was-validated` + 瀏覽器原生驗證：它繞過框架的驗證狀態，兩套錯誤來源會打架。
- ❌ 自己刻 `<span class="text-danger">` 當錯誤訊息：`.invalid-feedback` 已經處理好顯示時機與樣式。
- ❌ 把 `.invalid-feedback` 放在 input **前面**：sibling 選擇器不成立，訊息永遠不顯示。
