import { bootstrapApplication } from '@angular/platform-browser'
import { appConfig } from './app/app.config'
import { AppComponent } from './app/app.component'

// 漸進增強旗標：全站捲動進場動畫（見 src/styles/_animations.scss）預設不隱藏內容，
// 只有這支主程式真的開始執行時才加上 anim-ready，CSS 才會套用「隱藏 → 進場」的初始態。
// 放在 bootstrapApplication 呼叫之前、Angular 尚未渲染任何內容時執行，避免內容閃現後又被藏起來；
// 若這支 bundle 因為老舊瀏覽器或內嵌瀏覽器而完全沒執行到，旗標就不會出現，賓客看到的會是動畫的最終可見態。
document.documentElement.classList.add('anim-ready')

bootstrapApplication(AppComponent, appConfig).catch((err) => console.error(err))
