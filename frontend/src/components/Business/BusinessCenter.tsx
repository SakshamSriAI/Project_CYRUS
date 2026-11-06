import React, { useEffect, useState } from 'react';

interface FinancialSummaryData {
  tenant_id: string;
  total_revenue_collected_inr: number;
  total_receivables_pending_inr: number;
  total_overdue_inr: number;
  active_client_count: number;
  active_project_count: number;
  collection_efficiency_percent: number;
  health_score: number;
  overdue_invoices_count: number;
}

interface InvoiceItem {
  id: string;
  tenant_id: string;
  client_id: string;
  client_name: string;
  invoice_number: string;
  amount_inr: number;
  status: 'PAID' | 'ISSUED' | 'OVERDUE' | 'DRAFT' | 'CANCELLED';
  issue_date: string;
  due_date: string;
  paid_date?: string | null;
  description?: string;
  days_overdue: number;
}

interface ClientItem {
  id: string;
  tenant_id: string;
  client_name: string;
  contact_email?: string;
  status: string;
  created_at: string;
  metadata?: Record<string, any>;
}

interface ProjectItem {
  id: string;
  tenant_id: string;
  client_name: string;
  name: string;
  status: string;
  budget_inr: number;
  progress_percent: number;
  deadline?: string;
}

export const BusinessCenter: React.FC = () => {
  const [selectedTenant, setSelectedTenant] = useState<string>('all');
  const [summary, setSummary] = useState<FinancialSummaryData | null>(null);
  const [invoices, setInvoices] = useState<InvoiceItem[]>([]);
  const [clients, setClients] = useState<ClientItem[]>([]);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [activeTab, setActiveTab] = useState<'invoices' | 'clients' | 'projects' | 'briefing'>('invoices');
  const [executiveReport, setExecutiveReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [followupDraft, setFollowupDraft] = useState<string | null>(null);

  const fetchBusinessData = async () => {
    setLoading(true);
    const tenantParam = selectedTenant !== 'all' ? `?tenant_id=${selectedTenant}` : '';
    try {
      const [sumRes, invRes, cliRes, projRes, repRes] = await Promise.all([
        fetch(`/api/v1/business/summary${tenantParam}`),
        fetch(`/api/v1/business/invoices${tenantParam}`),
        fetch(`/api/v1/business/clients${tenantParam}`),
        fetch(`/api/v1/business/projects${tenantParam}`),
        fetch(`/api/v1/business/health-report${tenantParam}`),
      ]);

      if (sumRes.ok) setSummary(await sumRes.json());
      if (invRes.ok) {
        const invData = await invRes.json();
        setInvoices(invData.invoices || []);
      }
      if (cliRes.ok) {
        const cliData = await cliRes.json();
        setClients(cliData.clients || []);
      }
      if (projRes.ok) {
        const projData = await projRes.json();
        setProjects(projData.projects || []);
      }
      if (repRes.ok) {
        const repData = await repRes.json();
        setExecutiveReport(repData.report || '');
      }
    } catch (e) {
      console.error('Failed to load business data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBusinessData();
  }, [selectedTenant]);

  const overdueInvoices = invoices.filter((i) => i.status === 'OVERDUE');

  const handleGenerateFollowup = (inv: InvoiceItem) => {
    const draft = (
      `SUBJECT: Friendly Reminder: Outstanding Invoice ${inv.invoice_number} - CYRUS Financial Services\n\n` +
      `Dear ${inv.client_name} Accounts Team,\n\n` +
      `We hope this message finds you well. This is a gentle notification regarding Invoice ${inv.invoice_number} ` +
      `for ₹${inv.amount_inr.toLocaleString('en-IN')}, which was due on ${inv.due_date} (${inv.days_overdue} days past due).\n\n` +
      `Scope Delivered: ${inv.description || 'Enterprise Technology Services'}.\n\n` +
      `Please let us know if you require any updated payment details. Thank you for your continued partnership.\n\n` +
      `Warm regards,\n` +
      `Saksham Srivastava & CYRUS Business Operations`
    );
    setFollowupDraft(draft);
  };

  return (
    <div className="glass-panel p-5 mb-6 border border-emerald-800/40">
      {/* Header & Tenant Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">💼</span>
            <h2 className="text-lg font-bold text-slate-100">CYRUS Business Intelligence & Multi-Tenant Telemetry</h2>
            <span className="badge-tag mono text-emerald-400 bg-emerald-950/60 border-emerald-700/60">PHASE 8</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time accounts receivable, multi-tenant client boundary isolation, zero-hallucination overdue audits, and financial health scoring.
          </p>
        </div>

        {/* Tenant Filter Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Tenant Sandbox:</span>
          <select
            value={selectedTenant}
            onChange={(e) => setSelectedTenant(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-cyan-300 font-mono focus:outline-none focus:border-cyan-500"
          >
            <option value="all">Global (All Tenants)</option>
            <option value="apex_corp">Apex Consulting (apex_corp)</option>
            <option value="nexus_tech">Nexus AI Systems (nexus_tech)</option>
            <option value="solaris_media">Solaris Digital Media (solaris_media)</option>
          </select>
          <button
            onClick={fetchBusinessData}
            disabled={loading}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition-colors"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 my-4">
          {/* Revenue Realized */}
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-emerald-800/40">
            <span className="text-[11px] text-slate-400 block mb-1">Realized Revenue (PAID)</span>
            <span className="text-lg font-bold text-emerald-400 mono">
              ₹{summary.total_revenue_collected_inr.toLocaleString('en-IN')}
            </span>
            <span className="text-[10px] text-emerald-500 block mono mt-0.5">100% Realized Cashflow</span>
          </div>

          {/* Overdue Receivables Alert */}
          <div className={`p-3.5 rounded-lg border ${
            summary.total_overdue_inr > 0 ? 'bg-rose-950/30 border-rose-800/60' : 'bg-slate-900/80 border-slate-800'
          }`}>
            <span className="text-[11px] text-slate-400 block mb-1">Overdue Receivables</span>
            <span className={`text-lg font-bold mono ${summary.total_overdue_inr > 0 ? 'text-rose-400' : 'text-slate-300'}`}>
              ₹{summary.total_overdue_inr.toLocaleString('en-IN')}
            </span>
            <span className="text-[10px] text-rose-400/90 block mono mt-0.5">
              {summary.overdue_invoices_count} invoices past due
            </span>
          </div>

          {/* Pending In-Flight */}
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-amber-800/40">
            <span className="text-[11px] text-slate-400 block mb-1">Pending Receivables (ISSUED)</span>
            <span className="text-lg font-bold text-amber-400 mono">
              ₹{summary.total_receivables_pending_inr.toLocaleString('en-IN')}
            </span>
            <span className="text-[10px] text-amber-500/90 block mono mt-0.5">Active billing cycles</span>
          </div>

          {/* Financial Health Index */}
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-cyan-800/40">
            <span className="text-[11px] text-slate-400 block mb-1">Financial Health Index</span>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-cyan-400 mono">{summary.health_score}</span>
              <span className="text-xs text-slate-400 mono">/ 100</span>
            </div>
            <span className="text-[10px] text-cyan-300 block mono mt-0.5">
              {summary.collection_efficiency_percent}% Realization Ratio
            </span>
          </div>
        </div>
      )}

      {/* Critical Overdue Alert Notice */}
      {overdueInvoices.length > 0 && (
        <div className="mb-4 p-3 rounded-lg bg-rose-950/40 border border-rose-800/60">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-rose-300 flex items-center gap-1.5">
              <span>⚠️</span>
              <span>Action Required: {overdueInvoices.length} Invoices Overdue</span>
            </span>
            <span className="text-[10px] mono text-rose-400 bg-rose-900/50 px-2 py-0.5 rounded">
              Audited from SQLite WAL
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {overdueInvoices.map((inv) => (
              <div
                key={inv.id}
                className="p-2.5 rounded bg-slate-900/80 border border-rose-900/60 flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-200">
                    <span className="text-rose-400 mono mr-1.5">{inv.invoice_number}</span>
                    <span>{inv.client_name}</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    Amount: <strong className="text-white">₹{inv.amount_inr.toLocaleString('en-IN')}</strong> · Due: {inv.due_date} ({inv.days_overdue} days past due)
                  </div>
                </div>
                <button
                  onClick={() => handleGenerateFollowup(inv)}
                  className="px-2.5 py-1 rounded bg-rose-900/60 hover:bg-rose-800 text-rose-200 text-[11px] font-medium shrink-0 ml-2"
                >
                  Draft Reminder
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Follow-up Draft Modal / Window */}
      {followupDraft && (
        <div className="mb-4 p-4 rounded-lg bg-slate-900/95 border border-cyan-800/60">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-cyan-300">Generated Payment Follow-up Notice</span>
            <button
              onClick={() => setFollowupDraft(null)}
              className="text-slate-400 hover:text-white text-xs px-2 py-0.5 rounded bg-slate-800"
            >
              Close
            </button>
          </div>
          <pre className="text-xs text-slate-200 font-mono bg-slate-950 p-3 rounded border border-slate-800 overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {followupDraft}
          </pre>
        </div>
      )}

      {/* Tabs Control */}
      <div className="flex border-b border-slate-800 mb-3 text-xs font-medium gap-1">
        <button
          onClick={() => setActiveTab('invoices')}
          className={`px-3 py-2 border-b-2 transition-colors ${
            activeTab === 'invoices' ? 'border-cyan-500 text-cyan-300 font-semibold' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Invoices Ledger ({invoices.length})
        </button>
        <button
          onClick={() => setActiveTab('clients')}
          className={`px-3 py-2 border-b-2 transition-colors ${
            activeTab === 'clients' ? 'border-cyan-500 text-cyan-300 font-semibold' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Client CRM ({clients.length})
        </button>
        <button
          onClick={() => setActiveTab('projects')}
          className={`px-3 py-2 border-b-2 transition-colors ${
            activeTab === 'projects' ? 'border-cyan-500 text-cyan-300 font-semibold' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Projects & Milestones ({projects.length})
        </button>
        <button
          onClick={() => setActiveTab('briefing')}
          className={`px-3 py-2 border-b-2 transition-colors ${
            activeTab === 'briefing' ? 'border-cyan-500 text-cyan-300 font-semibold' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Executive Financial Briefing
        </button>
      </div>

      {/* --- TAB 1: INVOICES LEDGER --- */}
      {activeTab === 'invoices' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 mono">
                <th className="py-2 px-3">Invoice #</th>
                <th className="py-2 px-3">Enterprise Client</th>
                <th className="py-2 px-3">Amount (INR)</th>
                <th className="py-2 px-3">Status</th>
                <th className="py-2 px-3">Due Date</th>
                <th className="py-2 px-3">Scope Delivered</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {invoices.map((inv) => (
                <tr key={inv.id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="py-2.5 px-3 mono font-semibold text-cyan-300">{inv.invoice_number}</td>
                  <td className="py-2.5 px-3 text-slate-200 font-medium">{inv.client_name}</td>
                  <td className="py-2.5 px-3 mono text-white">₹{inv.amount_inr.toLocaleString('en-IN')}</td>
                  <td className="py-2.5 px-3">
                    {inv.status === 'PAID' && (
                      <span className="mono text-[10px] px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300">
                        PAID
                      </span>
                    )}
                    {inv.status === 'ISSUED' && (
                      <span className="mono text-[10px] px-2 py-0.5 rounded bg-amber-950/60 border border-amber-800 text-amber-300">
                        ISSUED (PENDING)
                      </span>
                    )}
                    {inv.status === 'OVERDUE' && (
                      <span className="mono text-[10px] px-2 py-0.5 rounded bg-rose-950/60 border border-rose-800 text-rose-300">
                        OVERDUE (+{inv.days_overdue}d)
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 px-3 mono text-slate-400">{inv.due_date}</td>
                  <td className="py-2.5 px-3 text-slate-400 truncate max-w-xs">{inv.description || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* --- TAB 2: CLIENT CRM --- */}
      {activeTab === 'clients' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {clients.map((c) => (
            <div key={c.id} className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-100">{c.client_name}</span>
                <span className="text-[10px] mono px-2 py-0.5 rounded bg-slate-800 text-cyan-300">
                  {c.tenant_id}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 space-y-1">
                <div>Contact: <span className="text-slate-200 mono">{c.contact_email || 'None'}</span></div>
                <div>Status: <span className="text-emerald-400 mono">{c.status}</span></div>
                {c.metadata && (
                  <div>Industry: <span className="text-slate-300">{c.metadata.industry || 'Enterprise'}</span></div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* --- TAB 3: PROJECTS --- */}
      {activeTab === 'projects' && (
        <div className="space-y-3">
          {projects.map((p) => (
            <div key={p.id} className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="text-xs font-bold text-slate-100 mr-2">{p.name}</span>
                  <span className="text-[11px] text-slate-400">({p.client_name})</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs mono text-white">Budget: ₹{p.budget_inr.toLocaleString('en-IN')}</span>
                  <span className="text-[10px] mono px-2 py-0.5 rounded bg-slate-800 text-cyan-300">
                    {p.status}
                  </span>
                </div>
              </div>
              {/* Progress bar */}
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-cyan-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${p.progress_percent}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-400 mono mt-1">
                <span>Milestone Progress: {p.progress_percent}%</span>
                <span>Deadline: {p.deadline || 'Ongoing'}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* --- TAB 4: EXECUTIVE BRIEFING --- */}
      {activeTab === 'briefing' && executiveReport && (
        <div className="p-4 rounded-lg bg-slate-900/90 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-emerald-300 uppercase tracking-wider">
              Automated Business Financial Health Briefing
            </span>
            <span className="text-[10px] mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
              ZERO HALLUCINATION AUDIT
            </span>
          </div>
          <p className="text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">{executiveReport}</p>
        </div>
      )}
    </div>
  );
};
