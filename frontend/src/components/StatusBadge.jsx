import React from 'react';
import { CheckCircle2, AlertTriangle, GitCompare, HelpCircle } from 'lucide-react';

export const StatusBadge = ({ status, size = 'md' }) => {
  const normalized = (status || '').toUpperCase();

  const configs = {
    CURRENT: {
      bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      icon: CheckCircle2,
      label: 'CURRENT',
      dot: 'bg-emerald-400'
    },
    OUTDATED: {
      bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      icon: AlertTriangle,
      label: 'OUTDATED',
      dot: 'bg-rose-400'
    },
    CONFLICTING: {
      bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      icon: GitCompare,
      label: 'CONFLICTING',
      dot: 'bg-amber-400'
    },
    UNCERTAIN: {
      bg: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
      icon: HelpCircle,
      label: 'UNCERTAIN',
      dot: 'bg-indigo-400'
    },
  };

  const current = configs[normalized] || {
    bg: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
    icon: HelpCircle,
    label: normalized || 'UNKNOWN',
    dot: 'bg-slate-400'
  };

  const Icon = current.icon;
  const isLarge = size === 'lg';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium border rounded-full transition-all ${
        current.bg
      } ${isLarge ? 'px-3.5 py-1.5 text-sm tracking-wider' : 'px-2.5 py-1 text-xs'}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${current.dot}`}></span>
      <Icon className={isLarge ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
      <span>{current.label}</span>
    </span>
  );
};

export default StatusBadge;
