import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload, 
  TrendingUp, 
  Layers, 
  PieChart as PieIcon, 
  Repeat, 
  Lightbulb, 
  ArrowUpRight, 
  ArrowDownRight,
  Trash2,
  Download,
  AlertTriangle,
  Clock,
  Search,
  Sparkles,
  CreditCard
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  Cell,
  Tooltip as ChartTooltip,
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  LineChart, 
  Line, 
  CartesianGrid
} from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const CATEGORIES = [
  "Food", "Travel", "Shopping", "Bills", "EMI", 
  "Subscriptions", "Salary", "Rent", "Investments", "Other"
];

const CATEGORY_COLORS: Record<string, string> = {
  Food: "#f87171",
  Travel: "#60a5fa",
  Shopping: "#f472b6",
  Bills: "#fbbf24",
  EMI: "#a78bfa",
  Subscriptions: "#e879f9",
  Salary: "#34d399",
  Rent: "#38bdf8",
  Investments: "#2dd4bf",
  Other: "#cbd5e1"
};

export default function App() {
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Dashboard states
  const [transactions, setTransactions] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [recurring, setRecurring] = useState<any[]>([]);
  const [insights, setInsights] = useState<string[]>([]);
  
  // Filtering/sorting states
  const [activeTab, setActiveTab] = useState<string>("summary");
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [recurringFilter, setRecurringFilter] = useState("all");

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Mouse hover coordinate listeners for metallic shine cards
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    card.style.setProperty('--mouse-x', `${x}px`);
    card.style.setProperty('--mouse-y', `${y}px`);
  };

  // Auto-load session from URL if present
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlSessionId = params.get('session_id') || params.get('session');
    if (urlSessionId) {
      loadSessionData(urlSessionId);
    }
  }, []);

  // Poll session status helper
  const pollSessionStatus = async (sessionId: string) => {
    try {
      const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
      if (!res.ok) throw new Error("Failed to check status");
      const data = await res.json();
      
      if (data.status === "ready") {
        await loadSessionData(sessionId);
      } else if (data.status === "failed") {
        setError(data.error_message || "Statement processing failed.");
        setLoading(false);
      } else {
        setTimeout(() => pollSessionStatus(sessionId), 1500);
      }
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  // Load all session data
  const loadSessionData = async (sessionId: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const statusRes = await fetch(`${API_BASE}/sessions/${sessionId}`);
      if (!statusRes.ok) throw new Error("Session not found");
      const statusData = await statusRes.json();
      setSession(statusData);

      const [txnsRes, analyticsRes, insightsRes, recurringRes] = await Promise.all([
        fetch(`${API_BASE}/sessions/${sessionId}/transactions`),
        fetch(`${API_BASE}/sessions/${sessionId}/analytics`),
        fetch(`${API_BASE}/sessions/${sessionId}/insights`),
        fetch(`${API_BASE}/sessions/${sessionId}/recurring`)
      ]);

      if (!txnsRes.ok || !analyticsRes.ok || !insightsRes.ok || !recurringRes.ok) {
        throw new Error("Failed to load dashboard metrics");
      }

      const txns = await txnsRes.json();
      const analyticsData = await analyticsRes.json();
      const insightsData = await insightsRes.json();
      const recurringData = await recurringRes.json();

      setTransactions(txns);
      setAnalytics(analyticsData);
      setInsights(insightsData);
      setRecurring(recurringData);
      
      setLoading(false);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  // Handle file upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    const file = files[0];
    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to process bank statement.");
      }

      const data = await res.json();
      if (data.status === "ready") {
        await loadSessionData(data.session_id);
      } else {
        pollSessionStatus(data.session_id);
      }
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  // Category Override Handler
  const handleCategoryOverride = async (txnId: string, newCategory: string) => {
    if (!session) return;
    try {
      const res = await fetch(`${API_BASE}/sessions/${session.id}/transactions/${txnId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category: newCategory })
      });
      
      if (!res.ok) throw new Error("Failed to override category");
      await loadSessionData(session.id);
    } catch (err: any) {
      alert(err.message);
    }
  };

  // Purge Session
  const handleClearSession = async () => {
    if (!session) return;
    if (!confirm("Are you sure you want to purge all statement data from the server?")) return;
    
    try {
      await fetch(`${API_BASE}/sessions/${session.id}`, { method: "DELETE" });
      setSession(null);
      setTransactions([]);
      setAnalytics(null);
      setRecurring([]);
      setInsights([]);
      setActiveTab("summary");
    } catch (err) {
      console.error(err);
    }
  };

  // Filtered transactions
  const filteredTransactions = transactions.filter(t => {
    const matchesSearch = 
      t.description_clean.toLowerCase().includes(searchTerm.toLowerCase()) || 
      t.description_raw.toLowerCase().includes(searchTerm.toLowerCase());
      
    const matchesCategory = categoryFilter === "all" || t.category === categoryFilter;
    const matchesType = typeFilter === "all" || t.type === typeFilter;
    
    let matchesRecurring = true;
    if (recurringFilter === "recurring") matchesRecurring = t.is_recurring;
    else if (recurringFilter === "one-off") matchesRecurring = !t.is_recurring;
    
    return matchesSearch && matchesCategory && matchesType && matchesRecurring;
  });

  return (
    <div className="max-w-[1240px] mx-auto px-6 py-12 min-h-screen selection:bg-indigo-500/35 selection:text-white">
      {/* Screen-only content */}
      <div className="print:hidden">
        {/* Top Header */}
        <header className="flex justify-between items-center mb-12">
          <div className="flex items-center gap-3">
          <div className="w-3 h-3 bg-teal-400 rounded-full shadow-[0_0_15px_#2dd4bf] animate-[pulse_2s_infinite]"></div>
          <h1 className="text-3xl font-display font-bold tracking-tight bg-gradient-to-r from-white via-zinc-300 to-zinc-500 bg-clip-text text-transparent">
            RupeeRadar
          </h1>
        </div>
        
        {session && (
          <div className="flex gap-4">
            <button 
              className="flex items-center gap-2 px-4 py-2.5 bg-red-950/10 text-red-400 border border-red-500/10 rounded-xl text-xs font-semibold tracking-wider uppercase transition-all duration-300 hover:bg-red-950/20 hover:border-red-500/30"
              onClick={handleClearSession}
            >
              <Trash2 size={14} />
              Purge Session
            </button>
            <button 
              className="flex items-center gap-2 px-4 py-2.5 bg-white/[0.03] border border-white/5 rounded-xl text-xs font-semibold tracking-wider uppercase transition-all duration-300 hover:bg-white/[0.08] hover:border-white/10 hover:shadow-lg"
              onClick={() => window.print()}
            >
              <Download size={14} />
              Export PDF
            </button>
          </div>
        )}
      </header>

      {/* Error Alert */}
      {error && (
        <div className="flex gap-4 items-start p-5 bg-red-950/15 border border-red-500/20 rounded-2xl mb-8 animate-fade-in print-hide">
          <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={22} />
          <div>
            <h4 className="font-semibold text-red-200">Analysis Error</h4>
            <p className="text-sm text-red-300/80 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center min-h-[400px]">
          <div className="w-12 h-12 border-[3px] border-indigo-500 border-t-transparent rounded-full animate-spin glow-indigo"></div>
          <p className="mt-8 text-zinc-400 font-semibold text-sm tracking-wide">
            Analyzing and extracting your cash flow pipeline...
          </p>
        </div>
      )}

      {/* Landing State */}
      {!session && !loading && (
        <div className="max-w-[580px] mx-auto mt-16 space-y-8 animate-fade-in print-hide">
          <div className="cred-glass rounded-3xl p-8 text-center border border-white/5 relative overflow-hidden">
            <div className="absolute -top-10 -right-10 w-24 h-24 bg-teal-500/10 rounded-full blur-xl"></div>
            <Sparkles size={36} className="text-teal-400 mx-auto mb-4 animate-pulse" />
            <h2 className="text-2xl font-display font-bold text-white mb-2 tracking-tight">The Premium Finance Radar</h2>
            <p className="text-zinc-400 text-sm leading-relaxed max-w-sm mx-auto">
              Safely parse your bank statements. Upload files to calculate monthly cash flows, isolate subscription cycles, and receive direct observations.
            </p>
          </div>
          
          <div 
            className="border border-white/5 rounded-3xl p-16 text-center cursor-pointer transition-all duration-500 bg-gradient-to-b from-white/[0.01] to-transparent hover:border-indigo-500/30 hover:bg-white/[0.02]"
            onClick={() => fileInputRef.current?.click()}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept=".csv,.xlsx,.xls"
              onChange={handleFileUpload}
            />
            <Upload className="w-12 h-12 text-indigo-400 mx-auto mb-5 animate-bounce" />
            <h3 className="text-lg font-semibold text-white mb-1">Select Bank Statement</h3>
            <p className="text-xs text-zinc-500">Drag & drop or browse .csv, .xlsx, or .xls files</p>
          </div>
        </div>
      )}

      {/* Active Dashboard */}
      {session && !loading && analytics && (
        <div className="space-y-10">
          {/* Metadata Bar */}
          <div className="cred-glass rounded-2xl px-6 py-4 flex justify-between items-center text-xs text-zinc-400 border border-white/5">
            <div className="flex items-center gap-2">
              <Clock size={14} className="text-teal-400" />
              <span>Loaded File: <strong className="text-white">{session.filename}</strong></span>
            </div>
            <div className="text-zinc-500 font-medium">
              Data expiry TTL: {new Date(session.expires_at).toLocaleString()}
            </div>
          </div>

          {/* CRED Aesthetic Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div 
              className="cred-card rounded-2xl p-6 border border-white/5"
              onMouseMove={handleMouseMove}
            >
              <div className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest mb-3 flex justify-between items-center">
                <span>Inflow Total</span>
                <ArrowUpRight size={14} className="text-emerald-400" />
              </div>
              <div className="text-3xl font-display font-bold text-white tracking-tight">
                ₹{analytics.metrics.total_income.toLocaleString()}
              </div>
              <div className="text-[10px] text-zinc-500 mt-2 font-medium">Salary & deposits</div>
            </div>

            <div 
              className="cred-card rounded-2xl p-6 border border-white/5"
              onMouseMove={handleMouseMove}
            >
              <div className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest mb-3 flex justify-between items-center">
                <span>Outflow Total</span>
                <ArrowDownRight size={14} className="text-red-400" />
              </div>
              <div className="text-3xl font-display font-bold text-white tracking-tight">
                ₹{analytics.metrics.total_spend.toLocaleString()}
              </div>
              <div className="text-[10px] text-zinc-500 mt-2 font-medium">Spendings & debits</div>
            </div>

            <div 
              className="cred-card rounded-2xl p-6 border border-white/5"
              onMouseMove={handleMouseMove}
            >
              <div className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest mb-3 flex justify-between items-center">
                <span>Net Savings</span>
                <div className={`w-2 h-2 rounded-full ${analytics.metrics.savings >= 0 ? 'bg-emerald-400 shadow-[0_0_8px_#10b981]' : 'bg-red-400 shadow-[0_0_8px_#ef4444]'}`}></div>
              </div>
              <div className={`text-3xl font-display font-bold ${analytics.metrics.savings >= 0 ? 'text-emerald-400' : 'text-red-400'} tracking-tight`}>
                ₹{analytics.metrics.savings.toLocaleString()}
              </div>
              <div className="text-[10px] text-zinc-500 mt-2 font-medium">Balance delta</div>
            </div>

            <div 
              className="cred-card rounded-2xl p-6 border border-white/5"
              onMouseMove={handleMouseMove}
            >
              <div className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest mb-3 flex justify-between items-center">
                <span>Savings Rate</span>
                <TrendingUp size={14} className="text-teal-400" />
              </div>
              <div className="text-3xl font-display font-bold text-teal-400 tracking-tight">
                {analytics.metrics.savings_rate.toFixed(1)}%
              </div>
              <div className="text-[10px] text-zinc-500 mt-2 font-medium">Income to savings ratio</div>
            </div>
          </div>

          {/* Navigation Tab Bar */}
          <div className="flex gap-2 bg-[#0d1017]/80 border border-white/5 p-1 rounded-2xl w-fit print-hide cred-glass">
            <button 
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs uppercase tracking-wider font-bold transition-all duration-300 ${activeTab === 'summary' ? 'bg-white/[0.05] text-white border border-white/5 shadow-md' : 'text-zinc-500 hover:text-white'}`}
              onClick={() => setActiveTab('summary')}
            >
              <PieIcon size={14} className={activeTab === 'summary' ? 'text-indigo-400' : ''} /> Summary
            </button>
            <button 
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs uppercase tracking-wider font-bold transition-all duration-300 ${activeTab === 'transactions' ? 'bg-white/[0.05] text-white border border-white/5 shadow-md' : 'text-zinc-500 hover:text-white'}`}
              onClick={() => setActiveTab('transactions')}
            >
              <Layers size={14} className={activeTab === 'transactions' ? 'text-teal-400' : ''} /> Ledger
            </button>
            <button 
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs uppercase tracking-wider font-bold transition-all duration-300 ${activeTab === 'recurring' ? 'bg-white/[0.05] text-white border border-white/5 shadow-md' : 'text-zinc-500 hover:text-white'}`}
              onClick={() => setActiveTab('recurring')}
            >
              <Repeat size={14} className={activeTab === 'recurring' ? 'text-pink-400' : ''} /> Subscriptions ({recurring.length})
            </button>
            <button 
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs uppercase tracking-wider font-bold transition-all duration-300 ${activeTab === 'insights' ? 'bg-white/[0.05] text-white border border-white/5 shadow-md' : 'text-zinc-500 hover:text-white'}`}
              onClick={() => setActiveTab('insights')}
            >
              <Lightbulb size={14} className={activeTab === 'insights' ? 'text-amber-400' : ''} /> Observations ({insights.length})
            </button>
          </div>

          {/* TAB 1: SUMMARY PANELS */}
          {activeTab === 'summary' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              
              {/* Category distribution graph */}
              <div className="cred-glass rounded-2xl p-6 border border-white/5">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-6 flex items-center gap-2">
                  <PieIcon size={16} className="text-indigo-400" />
                  Category Outflows Breakdown
                </h3>
                <div className="h-[300px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart 
                      data={analytics.top_categories} 
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.02)" />
                      <XAxis type="number" stroke="#475569" fontSize={11} />
                      <YAxis dataKey="category" type="category" stroke="#475569" width={90} fontSize={11} />
                      <ChartTooltip 
                        contentStyle={{ backgroundColor: '#0d1017', borderColor: 'rgba(255,255,255,0.05)', borderRadius: '14px', fontSize: '12px' }}
                      />
                      <Bar dataKey="amount" fill="#6366f1" radius={[0, 4, 4, 0]}>
                        {analytics.top_categories.map((entry: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[entry.category] || "#6366f1"} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Monthly trend line */}
              <div className="cred-glass rounded-2xl p-6 border border-white/5">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-6 flex items-center gap-2">
                  <TrendingUp size={16} className="text-teal-400" />
                  Monthly Spend Trends
                </h3>
                <div className="h-[300px] w-full">
                  {analytics.monthly_trend && analytics.monthly_trend.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={analytics.monthly_trend}>
                        <defs>
                          <linearGradient id="trendGlow" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.2}/>
                            <stop offset="95%" stopColor="#14b8a6" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.02)" />
                        <XAxis dataKey="month" stroke="#475569" fontSize={11} />
                        <YAxis stroke="#475569" fontSize={11} />
                        <ChartTooltip 
                          contentStyle={{ backgroundColor: '#0d1017', borderColor: 'rgba(255,255,255,0.05)', borderRadius: '14px', fontSize: '12px' }}
                        />
                        <Line type="monotone" dataKey="spend" stroke="#14b8a6" strokeWidth={3.5} activeDot={{ r: 8, stroke: '#0a0b0e', strokeWidth: 2 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-zinc-500 text-sm">
                      Insufficient timeline intervals to plot trend lines
                    </div>
                  )}
                </div>
              </div>

              {/* Cash Flow Highlights */}
              <div className="cred-glass rounded-2xl p-6 border border-white/5 lg:col-span-2">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-5">Key Cash Flow Transactions</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {analytics.biggest_transactions.map((txn: any, i: number) => (
                    <div key={i} className="bg-white/[0.01] border border-white/5 rounded-2xl p-5 flex justify-between items-center transition-all duration-300 hover:border-white/10 hover:bg-white/[0.02]">
                      <div>
                        <div className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">
                          {txn.type === 'debit' ? 'Largest Debit Outflow' : 'Largest Credit Inflow'}
                        </div>
                        <div className="font-bold text-sm text-gray-200 mt-2">
                          {txn.description}
                        </div>
                        <div className="text-xs text-zinc-500 mt-0.5">
                          {txn.date}
                        </div>
                      </div>
                      <div className={`text-2xl font-display font-bold ${txn.type === 'debit' ? 'text-red-400' : 'text-emerald-400'}`}>
                        ₹{txn.amount.toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: TRANSACTION LEDGER */}
          {activeTab === 'transactions' && (
            <div className="cred-glass rounded-2xl p-6 border border-white/5 space-y-6">
              {/* LEDGER FILTER BAR */}
              <div className="flex flex-wrap gap-4 items-center">
                <div className="relative flex-1 min-w-[280px]">
                  <Search className="absolute left-3.5 top-3 text-zinc-500 w-4 h-4" />
                  <input 
                    type="text" 
                    placeholder="Search payee details or statement remarks..."
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    className="w-full bg-[#0d1017] border border-white/5 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-zinc-500 focus:border-indigo-500/50 focus:outline-none"
                  />
                </div>
                
                <select 
                  value={categoryFilter}
                  onChange={e => setCategoryFilter(e.target.value)}
                  className="bg-[#0d1017] border border-white/5 rounded-xl px-4 py-2.5 text-xs font-semibold text-zinc-400 uppercase tracking-wider focus:border-indigo-500/50 focus:outline-none cursor-pointer"
                >
                  <option value="all">All Categories</option>
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>

                <select 
                  value={typeFilter}
                  onChange={e => setTypeFilter(e.target.value)}
                  className="bg-[#0d1017] border border-white/5 rounded-xl px-4 py-2.5 text-xs font-semibold text-zinc-400 uppercase tracking-wider focus:border-indigo-500/50 focus:outline-none cursor-pointer"
                >
                  <option value="all">Credits & Debits</option>
                  <option value="debit">Debits Only</option>
                  <option value="credit">Credits Only</option>
                </select>

                <select 
                  value={recurringFilter}
                  onChange={e => setRecurringFilter(e.target.value)}
                  className="bg-[#0d1017] border border-white/5 rounded-xl px-4 py-2.5 text-xs font-semibold text-zinc-400 uppercase tracking-wider focus:border-indigo-500/50 focus:outline-none cursor-pointer"
                >
                  <option value="all">All Cycles</option>
                  <option value="recurring">Recurring</option>
                  <option value="one-off">One-off</option>
                </select>
              </div>

              {/* LEDGER DATA TABLE */}
              <div className="overflow-x-auto rounded-2xl border border-white/5 bg-black/10">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-white/5 text-zinc-500 font-semibold uppercase tracking-wider text-[10px]">
                      <th className="px-6 py-4">Date</th>
                      <th className="px-6 py-4">Clean Merchant</th>
                      <th className="px-6 py-4">Raw Reference</th>
                      <th className="px-6 py-4">Category Mapping</th>
                      <th className="px-6 py-4 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {filteredTransactions.map((t) => (
                      <tr key={t.id} className="ledger-row">
                        <td className="px-6 py-4 whitespace-nowrap text-zinc-500 text-xs">
                          {t.date}
                        </td>
                        <td className="px-6 py-4 font-bold text-gray-200">
                          <div className="flex items-center gap-2.5">
                            {t.description_clean}
                            {t.is_recurring && (
                              <span className="text-[9px] bg-indigo-500/10 text-indigo-300 px-2 py-0.5 rounded-full font-bold border border-indigo-500/20">
                                RECURRING
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-zinc-500 text-xs truncate max-w-[280px]" title={t.description_raw}>
                          {t.description_raw}
                        </td>
                        <td className="px-6 py-4">
                          <select 
                            value={t.category} 
                            onChange={(e) => handleCategoryOverride(t.id, e.target.value)}
                            className="bg-[#0d1017] border border-white/5 rounded-lg px-2.5 py-1 text-xs text-gray-300 focus:border-indigo-500/50 focus:outline-none cursor-pointer"
                            style={{ 
                              borderLeft: `3px solid ${CATEGORY_COLORS[t.category] || '#94a3b8'}`,
                              paddingLeft: '8px'
                            }}
                          >
                            {CATEGORIES.map(c => (
                              <option key={c} value={c}>{c}</option>
                            ))}
                          </select>
                        </td>
                        <td className={`px-6 py-4 text-right font-display font-bold text-base ${t.type === 'debit' ? 'text-red-400' : 'text-emerald-400'}`}>
                          {t.type === 'debit' ? '-' : '+'}₹{Math.abs(t.amount).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredTransactions.length === 0 && (
                  <div className="text-center py-12 text-zinc-500 text-sm">
                    No ledger entries matching current filter settings
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: RECURRING PANEL */}
          {activeTab === 'recurring' && (
            <div className="cred-glass rounded-2xl p-6 border border-white/5 space-y-6">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Repeat size={16} className="text-pink-400" />
                Subscriptions & recurring schedules
              </h3>
              
              {/* Virtual Credit Cards Style Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {recurring.map((group) => (
                  <div 
                    key={group.id} 
                    className="cred-card rounded-2xl p-6 border border-white/5 min-h-[170px] flex flex-col justify-between"
                    onMouseMove={handleMouseMove}
                  >
                    <div>
                      <div className="flex justify-between items-center mb-3">
                        <span className={`text-[9px] px-2.5 py-0.5 rounded-full cat-badge cat-${group.category}`}>
                          {group.category}
                        </span>
                        <CreditCard size={16} className="text-zinc-600" />
                      </div>
                      <h4 className="text-lg font-bold text-gray-200 tracking-tight">
                        {group.label}
                      </h4>
                      <p className="text-[10px] text-zinc-500 uppercase tracking-widest mt-0.5">
                        Recurring cycle: {group.frequency}
                      </p>
                    </div>
                    
                    <div className="mt-4 border-t border-white/[0.04] pt-4 flex justify-between items-end">
                      <div>
                        <div className="text-xs text-zinc-500 font-medium">Average charge</div>
                        <div className="text-2xl font-display font-bold text-white">
                          ₹{group.typical_amount.toLocaleString()}
                        </div>
                      </div>
                      <div className="text-[9px] text-zinc-500 text-right">
                        Last charged<br />
                        <span className="text-gray-300 font-semibold">{group.last_seen_date}</span>
                      </div>
                    </div>
                  </div>
                ))}
                
                {recurring.length === 0 && (
                  <div className="col-span-full text-center py-12 text-zinc-500 text-sm">
                    No recurring timelines detected.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: INSIGHT PANEL */}
          {activeTab === 'insights' && (
            <div className="cred-glass rounded-2xl p-6 border border-white/5 space-y-6">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Lightbulb size={16} className="text-amber-400" />
                AI Generated Spending Observations
              </h3>
              
              <div className="space-y-4">
                {insights.map((insight, i) => (
                  <div key={i} className="cred-card rounded-2xl p-5 border border-white/5 flex gap-4 items-start hover:border-amber-500/20">
                    <div className="w-8 h-8 rounded-full bg-amber-500/10 flex items-center justify-center shrink-0">
                      <Lightbulb size={14} className="text-amber-400 animate-pulse" />
                    </div>
                    <p className="text-gray-300 text-sm leading-relaxed font-medium">
                      {insight}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      </div>

      {/* PROFESSIONAL PRINT REPORT (HIDDEN ON SCREEN, VISIBLE ON PRINT) */}
      {session && analytics && (
        <div className="hidden print:block text-black bg-white p-6 space-y-8 font-sans">
          {/* Header */}
          <div className="border-b-2 border-gray-900 pb-4 flex justify-between items-end">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-gray-900">RUPEERADAR FINANCIAL REPORT</h1>
              <p className="text-sm text-gray-500 mt-1">AI-Powered personal statement audit & insights</p>
            </div>
            <div className="text-right text-xs text-gray-500">
              <div>Session ID: {session.id}</div>
              <div>Generated: {new Date().toLocaleDateString()}</div>
            </div>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 text-sm bg-gray-50 p-4 rounded-xl border border-gray-200">
            <div><strong>Statement File:</strong> {session.filename}</div>
            <div><strong>Session Created:</strong> {new Date(session.uploaded_at).toLocaleString()}</div>
          </div>

          {/* Metrics */}
          <div>
            <h2 className="text-lg font-bold border-b border-gray-300 pb-2 mb-4 text-gray-800 uppercase tracking-wide">Financial Cash Flow Metrics</h2>
            <div className="grid grid-cols-4 gap-4 text-center">
              <div className="border border-gray-200 rounded-xl p-3 bg-gray-50">
                <div className="text-xs text-gray-500 uppercase tracking-widest font-semibold">Total Inflow</div>
                <div className="text-xl font-bold text-emerald-600 mt-1">₹{analytics.metrics.total_income.toLocaleString()}</div>
              </div>
              <div className="border border-gray-200 rounded-xl p-3 bg-gray-50">
                <div className="text-xs text-gray-500 uppercase tracking-widest font-semibold">Total Outflow</div>
                <div className="text-xl font-bold text-red-600 mt-1">₹{analytics.metrics.total_spend.toLocaleString()}</div>
              </div>
              <div className="border border-gray-200 rounded-xl p-3 bg-gray-50">
                <div className="text-xs text-gray-500 uppercase tracking-widest font-semibold">Net Savings</div>
                <div className={`text-xl font-bold mt-1 ${analytics.metrics.savings >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                  ₹{analytics.metrics.savings.toLocaleString()}
                </div>
              </div>
              <div className="border border-gray-200 rounded-xl p-3 bg-gray-50">
                <div className="text-xs text-gray-500 uppercase tracking-widest font-semibold">Savings Rate</div>
                <div className="text-xl font-bold text-indigo-600 mt-1">{analytics.metrics.savings_rate.toFixed(1)}%</div>
              </div>
            </div>
          </div>

          {/* Observations & Insights */}
          <div className="break-inside-avoid">
            <h2 className="text-lg font-bold border-b border-gray-300 pb-2 mb-4 text-gray-800 uppercase tracking-wide">Smart Financial Observations</h2>
            <ul className="space-y-2 list-disc list-inside text-sm text-gray-700">
              {insights.map((insight, i) => (
                <li key={i} className="leading-relaxed">{insight}</li>
              ))}
            </ul>
          </div>

          {/* Detected Recurring Timelines */}
          <div className="break-inside-avoid">
            <h2 className="text-lg font-bold border-b border-gray-300 pb-2 mb-4 text-gray-800 uppercase tracking-wide">Detected Recurring Payments (Subscriptions & EMIs)</h2>
            {recurring.length > 0 ? (
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-gray-300 bg-gray-100 font-semibold text-gray-700">
                    <th className="px-4 py-2">Merchant Name</th>
                    <th className="px-4 py-2">Category</th>
                    <th className="px-4 py-2">Frequency</th>
                    <th className="px-4 py-2 text-right">Average Charge</th>
                    <th className="px-4 py-2 text-right">Latest Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {recurring.map((group) => (
                    <tr key={group.id} className="text-gray-600">
                      <td className="px-4 py-2 font-bold text-gray-800">{group.label}</td>
                      <td className="px-4 py-2">{group.category}</td>
                      <td className="px-4 py-2 uppercase">{group.frequency}</td>
                      <td className="px-4 py-2 text-right font-bold text-gray-800">₹{group.typical_amount.toLocaleString()}</td>
                      <td className="px-4 py-2 text-right">{group.last_seen_date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-sm text-gray-500 italic">No recurring timelines detected.</div>
            )}
          </div>

          {/* Full Transaction ledger */}
          <div className="page-break-before">
            <h2 className="text-lg font-bold border-b border-gray-300 pb-2 mb-4 text-gray-800 uppercase tracking-wide">Complete Transactions Ledger</h2>
            <table className="w-full text-left border-collapse text-[10px]">
              <thead>
                <tr className="border-b-2 border-gray-300 bg-gray-100 font-bold text-gray-700">
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2">Payee Detail</th>
                  <th className="px-3 py-2">Statement Remarks</th>
                  <th className="px-3 py-2">Category</th>
                  <th className="px-3 py-2 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {transactions.map((t) => (
                  <tr key={t.id} className="text-gray-600">
                    <td className="px-3 py-2 whitespace-nowrap">{t.date}</td>
                    <td className="px-3 py-2 font-semibold text-gray-800">{t.description_clean}</td>
                    <td className="px-3 py-2 text-gray-500 max-w-[240px] truncate">{t.description_raw}</td>
                    <td className="px-3 py-2">{t.category}</td>
                    <td className={`px-3 py-2 text-right font-bold ${t.type === 'debit' ? 'text-red-600' : 'text-emerald-600'}`}>
                      {t.type === 'debit' ? '-' : '+'}₹{Math.abs(t.amount).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
