import type { Metadata } from 'next';
import './globals.css';
export const metadata:Metadata={title:'复旦 · 校园空间｜三维校园与步行漫游',description:'实景复原的复旦校园，支持鸟瞰与室外步行漫游，空旷区域自由行走，建筑内部不开放'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="zh-CN"><body>{children}</body></html>}
