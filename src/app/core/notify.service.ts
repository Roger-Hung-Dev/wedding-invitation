import { Injectable } from '@angular/core'

/**
 * 全域提示的抽換介面。底層（core／api）需要提示使用者時注入這個 token，
 * 實際實作由 UI 元件庫層提供並在組合根綁定，換元件庫時底層不用改。
 */
@Injectable()
export abstract class NotifyService {
  abstract error(message: string): void
  abstract success(message: string): void
}
