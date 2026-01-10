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
          <main className="w-[90%] 2xl:w-[80%] max-w-screen-2xl mx-auto px-4 py-8">
            {children}
          </main>
        </CurrencyProvider>
      </body>
    </html>
  );
}
