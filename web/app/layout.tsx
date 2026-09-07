import type { Metadata } from 'next';
import './globals.css';
export const metadata:Metadata={title:'校园空间重现 · 本地三维浏览',description:'根据参考照片重建的可交互校园场景'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="zh-CN"><body>{children}</body></html>}
