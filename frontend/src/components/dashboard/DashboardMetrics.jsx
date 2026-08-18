import React from 'react';
import { DollarSign, ShoppingCart, Clock, AlertOctagon, AlertTriangle, PackageX, Boxes, PackageCheck, Truck, TrendingUp } from 'lucide-react';
import { formatCurrency } from '../../utils/formatters';

export default function DashboardMetrics({ orders = [], inventory = [], tasks = [], summary = {} }) {
  // Calculations
  const totalInventoryValue = inventory.reduce((sum, item) => {
    const price = item.product?.unit_price || 0;
    const qty = item.quantity || 0;
    return sum + (price * qty);
  }, 0);

  const totalOrders = orders.length;
  const pendingOrders = orders.filter(o => o.status === 'PENDING').length;
  const criticalOrders = orders.filter(o => o.priority_evaluation?.priority_level === 'CRITICAL' || o.priority === 'URGENT').length;

  let lowStockCount = 0;
  let outOfStockCount = 0;
  inventory.forEach(inv => {
    const avail = inv.available_quantity;
    const reorder = inv.product?.reorder_level || 10;
    if (avail <= 0) outOfStockCount++;
    else if (avail <= reorder) lowStockCount++;
  });

  const pickingQueue = orders.filter(o => ['ALLOCATED', 'PARTIALLY_ALLOCATED', 'PICKING'].includes(o.status)).length;
  const packingQueue = orders.filter(o => ['PICKED', 'PACKING'].includes(o.status)).length;
  const dispatchQueue = orders.filter(o => ['QC_PASSED', 'PACKED'].includes(o.status)).length;

  const completedOrders = orders.filter(o => ['DISPATCHED', 'COMPLETED'].includes(o.status)).length;
  const fulfillmentRate = totalOrders > 0 ? Math.round((completedOrders / totalOrders) * 100) : 100;

  const metrics = [
    { title: 'Total Inventory Value', value: formatCurrency(totalInventoryValue), icon: DollarSign, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
    { title: 'Total Orders', value: totalOrders, icon: ShoppingCart, color: 'text-sky-400', bg: 'bg-sky-500/10 border-sky-500/20' },
    { title: 'Pending Orders', value: pendingOrders, icon: Clock, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
    { title: 'Critical Orders', value: criticalOrders, icon: AlertOctagon, color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/20' },
    { title: 'Low Stock Items', value: lowStockCount, icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
    { title: 'Out of Stock Items', value: outOfStockCount, icon: PackageX, color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/20' },
    { title: 'Picking Queue', value: pickingQueue, icon: Boxes, color: 'text-sky-400', bg: 'bg-sky-500/10 border-sky-500/20' },
    { title: 'Packing Queue', value: packingQueue, icon: PackageCheck, color: 'text-indigo-400', bg: 'bg-indigo-500/10 border-indigo-500/20' },
    { title: 'Dispatch Queue', value: dispatchQueue, icon: Truck, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20' },
    { title: 'Fulfillment Rate', value: `${fulfillmentRate}%`, icon: TrendingUp, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      {metrics.map((m, idx) => {
        const Icon = m.icon;
        return (
          <div key={idx} className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col justify-between space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 truncate">{m.title}</span>
              <div className={`p-1.5 rounded-lg border ${m.bg}`}>
                <Icon className={`w-4 h-4 ${m.color}`} />
              </div>
            </div>
            <div className="text-xl font-bold text-slate-100">{m.value}</div>
          </div>
        );
      })}
    </div>
  );
}
