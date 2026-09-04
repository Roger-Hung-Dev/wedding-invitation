# 參考：自寫互動元件（不用 Bootstrap JS）

原則：**Bootstrap 的 class 當純樣式，開關狀態由框架的反應式變數控制**。

## Vue 3 — Modal

重點：`.modal` 要同時有 `.show` 與 `display: block`（用 `.d-block` utility 給），backdrop 要自己渲染，開啟時 `body` 要加 `.modal-open` 擋背景捲動。

```vue
<!-- src/components/AppModal.vue -->
<script setup lang="ts">
import { watch, onUnmounted } from 'vue'

const props = defineProps<{ open: boolean; title: string }>()
const emit = defineEmits<{ (e: 'close'): void }>()

// body 的 .modal-open 由本元件負責加/移，離開時務必還原
watch(
  () => props.open,
  (open) => document.body.classList.toggle('modal-open', open),
)
onUnmounted(() => document.body.classList.remove('modal-open'))
</script>

<template>
  <Teleport to="body">
    <template v-if="open">
      <div class="modal-backdrop show" />
      <div class="modal show d-block" role="dialog" @click.self="emit('close')">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">{{ title }}</h5>
              <button type="button" class="btn-close" @click="emit('close')" />
            </div>
            <div class="modal-body">
              <slot />
            </div>
          </div>
        </div>
      </div>
    </template>
  </Teleport>
</template>
```

> `@click.self` 讓點擊 `.modal` 本身（即 dialog 外圍）才關閉，點內容不會誤關。

## Angular — Dropdown

重點：`.dropdown-menu` 加 `.show` 即展開；「點外面關閉」要自己處理。

```ts
// src/app/shared/dropdown.component.ts
import { Component, ElementRef, inject, input, output, signal } from '@angular/core'

export interface DropdownItem {
  readonly id: string
  readonly label: string
}

@Component({
  selector: 'app-dropdown',
  host: { '(document:click)': 'onDocumentClick($event)' },
  template: `
    <div class="dropdown">
      <button class="btn btn-secondary dropdown-toggle" type="button" (click)="toggle()">
        {{ label() }}
      </button>
      <ul class="dropdown-menu" [class.show]="open()">
        @for (item of items(); track item.id) {
          <li>
            <button class="dropdown-item" type="button" (click)="select(item)">
              {{ item.label }}
            </button>
          </li>
        }
      </ul>
    </div>
  `,
})
export class DropdownComponent {
  private readonly host = inject(ElementRef<HTMLElement>)

  readonly label = input.required<string>()
  readonly items = input.required<readonly DropdownItem[]>()
  readonly selected = output<DropdownItem>()

  protected readonly open = signal(false)

  protected toggle(): void {
    this.open.update((v) => !v)
  }

  protected select(item: DropdownItem): void {
    this.selected.emit(item)
    this.open.set(false)
  }

  // 點擊元件以外的區域就收起來
  protected onDocumentClick(event: MouseEvent): void {
    if (!this.host.nativeElement.contains(event.target as Node)) {
      this.open.set(false)
    }
  }
}
```

## Collapse（兩框架共通）

`.collapse` 加 `.show` 即展開。Bootstrap 的高度轉場由它的 JS 負責，我們不引 JS，所以**沒有動畫**：

- 可接受無動畫 → 直接綁 `.show`，最簡單。
- 需要動畫 → 用框架自己的轉場（Vue 的 `<Transition>`、Angular 的 `@angular/animations`），不要試圖模仿 Bootstrap 的 JS 行為。

## 不要做的事

- ❌ `import 'bootstrap'` 或 `import { Modal } from 'bootstrap'`
- ❌ `data-bs-toggle` / `data-bs-target` / `data-bs-dismiss` 屬性
- ❌ 在框架管理的節點上直接 `classList.add('show')`（下次 re-render 會被蓋掉）
