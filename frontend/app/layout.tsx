import type { Metadata } from "next";
import "./globals.css";
import { CurrencyProvider } from "@/context/CurrencyContext";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "StockSim - Investment Simulator",
  description: "Learn to trade and manage portfolio",
  icons: {
    icon: "/logo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`antialiased bg-[#F5F5F7] text-[#1D1D1F] font-sans`}
      >
        <CurrencyProvider>
          <Navbar />
          <main className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </CurrencyProvider>
      </body>
    </html>
  );
}
