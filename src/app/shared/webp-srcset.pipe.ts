import { Pipe, PipeTransform } from '@angular/core'
import { webpSrcset } from '../core/image-variants'

/**
 * 樣板用：由原圖網址組出 WebP 縮圖的 srcset，放在 picture 的 source 上。
 * 支援 WebP 的瀏覽器依 sizes 挑最接近顯示尺寸的那一張；不支援的舊瀏覽器退回 img 的原圖。
 */
@Pipe({ name: 'webpSrcset' })
export class WebpSrcsetPipe implements PipeTransform {
  transform(url: string): string | null {
    return webpSrcset(url)
  }
}
