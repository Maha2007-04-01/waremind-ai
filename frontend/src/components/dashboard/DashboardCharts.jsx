import React from 'react';
import { 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  AreaChart, 
  Area 
} from 'recharts';

export default function DashboardCharts({ analyticsData, orders = [], inventory = [] }) {
  // 1. Orders by status
  const statusCounts = {};
  orders.forEach(o => {
    statusCounts[o.status] = (statusCounts[o.status] || 0) + 1;
  });
  const ordersByStatus = Object.keys(statusCounts).map(status => ({
    name: status,
    value: statusCounts[status]
  }));
  const PIE_COLORS = ['#38bdf8', '#818cf8', '#a78bfa', '#f43f5e', '#fbbf24', '#34d399', '#94a3b8'];

  // 2. Inventory Health Breakdown
  let inStockCount = 0;
  let lowStockCount = 0;
  let outOfStockCount = 0;
  let damagedCount = 0;

  inventory.forEach(inv => {
    const avail = inv.available_quantity;
    const reorder = inv.product?.reorder_level || 10;
    if (inv.damaged_quantity > 0) damagedCount++;
    if (avail <= 0) outOfStockCount++;
    else if (avail <= reorder) lowStockCount++;
    else inStockCount++;
  });

  const inventoryHealthData = [
    { name: 'Optimal Stock', count: inStockCount, fill: '#34d399' },
    { name: 'Low Stock', count: lowStockCount, fill: '#fbbf24' },
    { name: 'Out of Stock', count: outOfStockCount, fill: '#f43f5e' },
    { name: 'Damaged', count: damagedCount, fill: '#a78bfa' },
  ];

  // 3. Fulfillment Trend (Mock hourly trend curve based on created_at timestamp)
  const fulfillmentTrendData = [
    { time: '06:00', orders: 4, fulfilled: 3 },
    { time: '08:00', orders: 8, fulfilled: 7 },
    { time: '10:00', orders: 15, fulfilled: 12 },
    { time: '12:00', orders: 22, fulfilled: 18 },
    { time: '14:00', orders: 18, fulfilled: 16 },
    { time: '16:00', orders: 12, fulfilled: 11 },
    { time: '18:00', orders: 6, fulfilled: 6 },
  ];

  // 4. Warehouse Workload
  const workloadData = [
    { stage: 'Allocation', pending: orders.filter(o => o.status === 'PENDING').length },
    { stage: 'Picking', pending: orders.filter(o => ['ALLOCATED', 'PARTIALLY_ALLOCATED', 'PICKING'].includes(o.status)).length },
    { stage: 'Packing', pending: orders.filter(o => ['PICKED', 'PACKING'].includes(o.status)).length },
    { stage: 'QC Inspection', pending: orders.filter(o => ['PACKED', 'QC_FAILED'].includes(o.status)).length },
    { stage: 'Dispatch', pending: orders.filter(o => o.status === 'QC_PASSED').length },
  ];

  // 5. Exceptions by Type
  const exceptionTypeData = [
    { type: 'Stock Deficit', count: 4 },
    { type: 'Damaged Goods', count: 2 },
    { type: 'SLA Risk', count: 3 },
    { type: 'QC Failure', count: 1 },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Orders by Status */}
      <div className="bg-slate-950 p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
        <h3 className="font-semibold text-slate-200 text-sm mb-2">Order Fulfillment Status Breakdown</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={ordersByStatus}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={4}
                dataKey="value"
              >
                {ordersByStatus.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }} 
              />
              <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Inventory Health */}
      <div className="bg-slate-950 p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
        <h3 className="font-semibold text-slate-200 text-sm mb-2">Inventory Health & Risk Distribution</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={inventoryHealthData}>
              <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }} 
              />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {inventoryHealthData.map((entry, index) => (
                  <Cell key={`cell-bar-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Fulfillment Trend */}
      <div className="bg-slate-950 p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
        <h3 className="font-semibold text-slate-200 text-sm mb-2">Hourly Fulfillment Velocity Trend</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={fulfillmentTrendData}>
              <defs>
                <linearGradient id="colorOrders" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#38bdf8" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorFulfilled" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#34d399" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#34d399" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }} 
              />
              <Area type="monotone" dataKey="orders" stroke="#38bdf8" fillOpacity={1} fill="url(#colorOrders)" name="Orders Received" />
              <Area type="monotone" dataKey="fulfilled" stroke="#34d399" fillOpacity={1} fill="url(#colorFulfilled)" name="Orders Dispatched" />
              <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Warehouse Workload */}
      <div className="bg-slate-950 p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
        <h3 className="font-semibold text-slate-200 text-sm mb-2">Stage Workload Queue Distribution</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={workloadData} layout="vertical">
              <XAxis type="number" stroke="#64748b" fontSize={12} />
              <YAxis dataKey="stage" type="category" stroke="#64748b" fontSize={12} width={100} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }} 
              />
              <Bar dataKey="pending" fill="#818cf8" radius={[0, 6, 6, 0]} name="Pending Queue" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
