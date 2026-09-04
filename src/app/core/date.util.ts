export interface Countdown {
  readonly days: number
  readonly hours: number
  readonly minutes: number
  readonly seconds: number
  /** 目標時間是否已經過去。 */
  readonly isOver: boolean
}

/**
 * 計算距離目標時間的剩餘天／時／分／秒。
 * 目標時間已過時回傳全 0 並將 isOver 設為 true，呼叫端據此切換成婚期已過的顯示內容。
 */
export function calcCountdown(targetIso: string, nowMs: number): Countdown {
  const diff = new Date(targetIso).getTime() - nowMs
  if (diff <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0, isOver: true }
  }
  const totalSeconds = Math.floor(diff / 1000)
  const days = Math.floor(totalSeconds / 86400)
  const hours = Math.floor((totalSeconds % 86400) / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  return { days, hours, minutes, seconds, isOver: false }
}

/** 補零成兩位數字串，倒數計時格顯示用。 */
export function padTwoDigits(value: number): string {
  return value.toString().padStart(2, '0')
}
