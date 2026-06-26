'use client';

import React, { useState, useEffect } from 'react';
import { Key, Shield, Clock, Layers, ListFilter, Activity, Plus, Database, Copy, Check } from 'lucide-react';

interface ApiKeyConfig {
  id: string;
  name: string;
  keyValue: string;
  expiryDate: string;
  expiryTime: string;
  limit: number;
  used: number;
  selectedTools: string[];
}

interface SearchLog {
  id: string;
  timestamp: string;
  keyName: string;
  tool: string;
  query: string;
}

const AVAILABLE_TOOLS = [
  'adv', 'paytm', 'imei', 'calltracer', 'upi', 'ifsc', 'number', 
  'pincode', 'ip', 'challan', 'ff', 'bgmi', 'snap', 'email', 'vehicle', 'git', 'insta', 'tg', 'tgidinfo', 'numleak'
];

export default function Dashboard() {
  const [keys, setKeys] = useState<ApiKeyConfig[]>([]);
  const [logs, setLogs] = useState<SearchLog[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Form States
  const [formName, setFormName] = useState('');
  const [formLimit, setFormLimit] = useState(500);
  const [formDate, setFormDate] = useState('2026-12-31');
  const [formTime, setFormTime] = useState('23:59');
  const [formScope, setFormScope] = useState<'all' | 'custom'>('all');
  const [chosenTools, setChosenTools] = useState<string[]>([]);

  // Seed default data on load
  useEffect(() => {
    setKeys([
      {
        id: '1',
        name: 'Enterprise_Client_Alpha',
        keyValue: 'shayan_demo_key',
        expiryDate: '2026-12-31',
        expiryTime: '23:59',
        limit: 1000,
        used: 142,
        selectedTools: ['all']
      }
    ]);
    setLogs([
      { id: 'l1', timestamp: '2026-06-26 18:05:22', keyName: 'Enterprise_Client_Alpha', tool: 'number', query: 'num=9876543210' },
      { id: 'l2', timestamp: '2026-06-26 18:08:14', keyName: 'Enterprise_Client_Alpha', tool: 'upi', query: 'upi=example@ybl' }
    ]);
  }, []);

  const handleCreateKey = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName) return;

    const newKeyString = 'shayan_' + Math.random().toString(36).substring(2, 15);
    const newKey: ApiKeyConfig = {
      id: Date.now().toString(),
      name: formName,
      keyValue: newKeyString,
      expiryDate: formDate,
      expiryTime: formTime,
      limit: Number(formLimit),
      used: 0,
      selectedTools: formScope === 'all' ? ['all'] : [...chosenTools]
    };

    setKeys([newKey, ...keys]);
    setFormName('');
    setChosenTools([]);
    
    // Simulate system log creation
    setLogs(prev => [{
      id: Date.now().toString(),
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
      keyName: formName,
      tool: 'SYSTEM',
      query: `Generated new access token [Scope: ${formScope}]`
    }, ...prev]);
  };

  const toggleToolSelection = (tool: string) => {
    if (chosenTools.includes(tool)) {
      setChosenTools(chosenTools.filter(t => t !== tool));
    } else {
      setChosenTools([...chosenTools, tool]);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Premium Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50 transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Database className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                NEXUS GATEWAY
              </span>
              <p className="text-xs text-cyan-400 font-mono tracking-widest uppercase">BY SHAYAN_EXPLORER</p>
            </div>
          </div>
          <div className="flex items-center space-x-2 bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700/50 text-xs font-mono">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-slate-300">Vercel Edge Cluster Active</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Core Control Setup Forms */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Section: Key Creation Provisioning Profile */}
          <div className="lg:col-span-1 bg-slate-900/40 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 blur-[80px] pointer-events-none" />
            <div className="flex items-center space-x-2.5 mb-6">
              <Plus className="h-5 w-5 text-cyan-400" />
              <h2 className="text-lg font-semibold tracking-tight">Provision API Token</h2>
            </div>

            <form onSubmit={handleCreateKey} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">Identifier Name</label>
                <input 
                  type="text" required placeholder="e.g., Production_App_Key" value={formName} onChange={e => setFormName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 transition-colors placeholder:text-slate-600"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">Total Request Volume Limit</label>
                <input 
                  type="number" required min="1" value={formLimit} onChange={e => setFormLimit(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm font-mono text-slate-100 focus:outline-none focus:border-cyan-500 transition-colors"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">Expiry Date</label>
                  <input 
                    type="date" required value={formDate} onChange={e => setFormDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs font-mono text-slate-100 focus:outline-none focus:border-cyan-500 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">Expiry Time</label>
                  <input 
                    type="time" required value={formTime} onChange={e => setFormTime(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs font-mono text-slate-100 focus:outline-none focus:border-cyan-500 transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Endpoint Restrictions</label>
                <div className="grid grid-cols-2 gap-2 p-1 bg-slate-950 rounded-xl border border-slate-800 mb-3">
                  <button
                    type="button" onClick={() => setFormScope('all')}
                    className={`py-1.5 text-xs font-medium rounded-lg transition-all ${formScope === 'all' ? 'bg-slate-800 text-cyan-400 border border-slate-700/50' : 'text-slate-500 hover:text-slate-300'}`}
                  >
                    All Tools Allowed
                  </button>
                  <button
                    type="button" onClick={() => setFormScope('custom')}
                    className={`py-1.5 text-xs font-medium rounded-lg transition-all ${formScope === 'custom' ? 'bg-slate-800 text-cyan-400 border border-slate-700/50' : 'text-slate-500 hover:text-slate-300'}`}
                  >
                    Custom Whitelist
                  </button>
                </div>

                {formScope === 'custom' && (
                  <div className="max-h-36 overflow-y-auto border border-slate-900 rounded-xl p-2 bg-slate-950/50 space-y-1 grid grid-cols-2 gap-1">
                    {AVAILABLE_TOOLS.map(tool => (
                      <button
                        type="button" key={tool} onClick={() => toggleToolSelection(tool)}
                        className={`flex items-center space-x-2 p-1.5 rounded-lg text-xs transition-colors text-left border ${chosenTools.includes(tool) ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-transparent border-transparent text-slate-400 hover:bg-slate-900'}`}
                      >
                        <div className={`h-2 w-2 rounded-full ${chosenTools.includes(tool) ? 'bg-cyan-400' : 'bg-slate-700'}`} />
                        <span className="font-mono">{tool}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                type="submit"
                className="w-full mt-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium text-sm py-3 px-4 rounded-xl shadow-lg shadow-cyan-500/10 transition-all flex items-center justify-center space-x-2"
              >
                <Key className="h-4 w-4" />
                <span>Compile & Issue Token</span>
              </button>
            </form>
          </div>

          {/* Section: Live System Status Tokens Display */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm relative overflow-hidden">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-2.5">
                  <Shield className="h-5 w-5 text-emerald-400" />
                  <h2 className="text-lg font-semibold tracking-tight">Active Cryptographic Keys</h2>
                </div>
                <span className="text-xs font-mono px-2 py-1 rounded bg-slate-800 text-slate-400">{keys.length} Active tokens</span>
              </div>

              <div className="space-y-4 max-h-[460px] overflow-y-auto pr-1">
                {keys.map((k) => (
                  <div key={k.id} className="bg-slate-950 border border-slate-800/80 rounded-xl p-4 hover:border-slate-700 transition-colors space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-sm font-semibold text-slate-200 tracking-tight">{k.name}</h3>
                        <div className="flex items-center space-x-2 mt-1.5 font-mono text-xs">
                          <span className="text-slate-500">Token:</span>
                          <span className="text-cyan-400 select-all bg-slate-900 px-2 py-0.5 rounded border border-slate-800">{k.keyValue}</span>
                          <button 
                            onClick={() => copyToClipboard(k.keyValue, k.id)}
                            className="text-slate-400 hover:text-white p-1 transition-colors"
                          >
                            {copiedId === k.id ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                          </button>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-mono text-slate-400 block">Quota Execution Tracker</span>
                        <span className="text-sm font-semibold font-mono text-slate-100">{k.used} <span className="text-slate-600">/</span> {k.limit} Req</span>
                      </div>
                    </div>

                    <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-cyan-500 to-emerald-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${Math.min((k.used / k.limit) * 100, 100)}%` }}
                      />
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-900 text-xs">
                      <div className="flex items-center space-x-1.5 text-amber-400 font-mono">
                        <Clock className="h-3.5 w-3.5" />
                        <span>Expires: {k.expiryDate} @ {k.expiryTime}</span>
                      </div>
                      <div className="flex items-center space-x-1 text-slate-400 font-mono">
                        <Layers className="h-3.5 w-3.5 text-slate-500" />
                        <span className="truncate max-w-[240px]">
                          Allowed: {k.selectedTools.join(', ')}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Section: Live System Request Logs Tracking */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2.5">
              <Activity className="h-5 w-5 text-cyan-400" />
              <h2 className="text-lg font-semibold tracking-tight">Real-Time Search Inspection Streams</h2>
            </div>
            <div className="flex items-center space-x-2 text-xs text-slate-500 font-mono">
              <ListFilter className="h-3 w-3" />
              <span>Monitoring Incoming Proxy Vectors</span>
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-900 rounded-xl overflow-hidden font-mono text-xs">
            <div className="bg-slate-900/80 px-4 py-2.5 border-b border-slate-800 text-slate-400 grid grid-cols-12 gap-2 font-semibold">
              <div className="col-span-2">Timestamp</div>
              <div className="col-span-3">Target Key Identifier</div>
              <div className="col-span-2 text-cyan-400">Tool Triggered</div>
              <div className="col-span-5">Inspected Query Value</div>
            </div>
            <div className="divide-y divide-slate-900 max-h-60 overflow-y-auto">
              {logs.map((log) => (
                <div key={log.id} className="px-4 py-3 hover:bg-slate-900/30 transition-colors grid grid-cols-12 gap-2 items-center">
                  <div className="col-span-2 text-slate-500">{log.timestamp}</div>
                  <div className="col-span-3 text-slate-300 truncate font-semibold">{log.keyName}</div>
                  <div className="col-span-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${log.tool === 'SYSTEM' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'}`}>
                      {log.tool.toUpperCase()}
                    </span>
                  </div>
                  <div className="col-span-5 text-slate-400 select-all font-sans truncate bg-slate-900/40 px-2 py-1 rounded border border-slate-900/80">{log.query}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </main>

      {/* Branded Premium Footer */}
      <footer className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 border-t border-slate-900 text-center text-xs text-slate-600 font-mono tracking-wide">
        &copy; 2026 NEXUS METRICS GATEWAY. ARCHITECTED BY <span className="text-slate-400 font-bold">SHAYAN_EXPLORER</span>. DEPLOYED NATIVELY ON VERCEL.
      </footer>
    </div>
  );
}
