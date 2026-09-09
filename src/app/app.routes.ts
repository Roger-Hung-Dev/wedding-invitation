import { Routes } from '@angular/router'
import { HomeComponent } from './features/home/home.component'

/**
 * 兩個宴席版本各自一個網址。
 *
 * 之所以能用路由而不是查詢字串，是因為建置設定是 outputMode: "static" ——
 * 每個路由都會在建置時產出一份實體的 HTML（vegetarian/index.html），
 * GitHub Pages 這類純靜態託管才送得出來。改用一般 SPA 的動態路由的話，
 * 直接開 /vegetarian 會 404，得靠 404.html 轉址那種取巧作法。
 *
 * 葷食是預設版本，走原本的網址；素食賓客才需要拿到 /vegetarian 這個連結。
 * 這樣既有的連結不會失效，而且要記得換連結的只有少數人。
 */
export const routes: Routes = [
  {
    path: '',
    component: HomeComponent,
    data: { diet: 'regular' },
  },
  {
    path: 'vegetarian',
    component: HomeComponent,
    data: { diet: 'vegetarian' },
  },
  {
    path: '**',
    redirectTo: '',
  },
]
