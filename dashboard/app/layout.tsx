import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
    title: 'Trinity Dashboard v2',
    description: 'Chat-First AGI Interface',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="ko">
            <body>{children}</body>
        </html>
    )
}
