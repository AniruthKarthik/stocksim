import Link from "next/link";
import Button from "@/components/Button";
import Card from "@/components/Card";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center max-w-2xl mx-auto space-y-8">
      <div className="space-y-4">
        <h1 className="text-5xl font-extrabold tracking-tight text-gray-900">
          Master the <span className="text-primary">Market</span> without the Risk
        </h1>
        <p className="text-xl text-gray-600">
          Experience real-time stock simulation with historical data. 
          Build your portfolio, track your growth, and learn investment strategies.
        </p>
      </div>

      <Card className="w-full p-8 bg-white/50 backdrop-blur-sm border-gray-200">
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/simulation/start" className="w-full sm:w-auto">
            <Button className="w-full text-lg py-3 px-8">
              Start New Simulation
            </Button>
          </Link>
          
          {/* Future: specific Check if session exists logic */}
          <Link href="/simulation" className="w-full sm:w-auto">
             <Button variant="secondary" className="w-full text-lg py-3 px-8">
               Continue Session
             </Button>
          </Link>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left w-full mt-12">
        {[
          { title: "Real Data", desc: "Based on actual historical market movements." },
          { title: "Zero Risk", desc: "Practice with virtual currency, learn safely." },
          { title: "Track Growth", desc: "Visualize your portfolio performance over time." },
        ].map((item, i) => (
          <div key={i} className="p-4 rounded-lg bg-white border border-gray-100 shadow-sm">
            <h3 className="font-bold text-gray-800 mb-2">{item.title}</h3>
            <p className="text-sm text-gray-600">{item.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}