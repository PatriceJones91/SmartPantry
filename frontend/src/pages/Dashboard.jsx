import { useEffect, useMemo, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { api } from "../api/client.js";
import StatCard from "../components/StatCard.jsx";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

const CATEGORY_COLORS = {
  Protein: "#ef4444",
  Dairy: "#facc15",
  Grain: "#a855f7",
  Fruit: "#ec4899",
  Breakfast: "#f97316",
  Vegetable: "#22c55e",
  "Canned Goods": "#10b981",
  Frozen: "#60a5fa",
  Snack: "#f97316",
  Condiment: "#92400e",
  "Tea & Coffee": "#6b7280",
  Other: "#d1d5db",
};

const COMMON_GROCERY_ITEMS = [
  { name: "eggs", category: "Protein" },
  { name: "milk", category: "Dairy" },
  { name: "bread", category: "Grain" },
  { name: "rice", category: "Grain" },
  { name: "chicken", category: "Protein" },
  { name: "cheese", category: "Dairy" },
  { name: "lettuce", category: "Vegetable" },
  { name: "tomatoes", category: "Vegetable" },
  { name: "beans", category: "Canned Goods" },
  { name: "pasta", category: "Grain" },
];

function normalize(text) {
  return String(text || "").trim().toLowerCase();
}

function daysUntil(dateString) {
  if (!dateString) return null;

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const exp = new Date(dateString);
  exp.setHours(0, 0, 0, 0);

  return Math.ceil((exp - today) / (1000 * 60 * 60 * 24));
}

function getAlertInfo(days) {
  if (days === null || days === undefined) return null;

  if (days <= 1) {
    return {
      label: "Use Immediately!!",
      className: "alertDanger",
      detail: `${days} day(s) left`,
    };
  }

  if (days <= 4) {
    return {
      label: "Warning Use Soon!",
      className: "alertWarning",
      detail: `${days} day(s) left`,
    };
  }

  if (days <= 10) {
    return {
      label: "Plan Ahead",
      className: "alertPlan",
      detail: `${days} day(s) left`,
    };
  }

  return null;
}

function renderPieLabel({ name, percent }) {
  const percentage = Math.round(percent * 100);
  return `${name} ${percentage}%`;
}

export default function Dashboard() {
  const user = getUser();
  const [pantry, setPantry] = useState([]);
  const [surveyStatus, setSurveyStatus] = useState({ pre: false, post: false });
  const [loading, setLoading] = useState(true);

  async function loadDashboard() {
    setLoading(true);
    try {
      const [pantryData, statusData] = await Promise.all([
        api.getPantry(user.id),
        api.getSurveyStatus(user.id),
      ]);

      setPantry(pantryData || []);
      setSurveyStatus(statusData || { pre: false, post: false });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, [user.id]);

  const activePantry = useMemo(() => {
    return pantry.filter((item) => item.status !== "deleted");
  }, [pantry]);

  const totalAmount = useMemo(() => {
    return activePantry.reduce((sum, item) => {
      return sum + Number(item.quantity || 0);
    }, 0);
  }, [activePantry]);

  const categoryData = useMemo(() => {
    const counts = {};

    activePantry.forEach((item) => {
      const category = item.category || "Other";
      counts[category] = (counts[category] || 0) + 1;
    });

    return Object.entries(counts).map(([name, value]) => ({
      name,
      value,
      fill: CATEGORY_COLORS[name] || CATEGORY_COLORS.Other,
    }));
  }, [activePantry]);

  const expirationAlerts = useMemo(() => {
    return activePantry
      .map((item) => {
        const days = daysUntil(item.expiration_date);
        const alert = getAlertInfo(days);

        return {
          ...item,
          days,
          alert,
        };
      })
      .filter((item) => item.alert)
      .sort((a, b) => a.days - b.days);
  }, [activePantry]);

  const grocerySuggestions = useMemo(() => {
    const pantryNames = activePantry.map((item) => normalize(item.item_name));

    const missingBasics = COMMON_GROCERY_ITEMS.filter((basic) => {
      return !pantryNames.some(
        (itemName) =>
          itemName.includes(normalize(basic.name)) ||
          normalize(basic.name).includes(itemName)
      );
    });

    return missingBasics.slice(0, 6);
  }, [activePantry]);

  return (
    <div>
      <div className="pageHeader dashboardHero">
        <div>
          <h1>Smart Pantry Dashboard</h1>
          <p>
            This is your quick view of pantry status, survey progress, expiration alerts,
            and suggested grocery needs.
          </p>
        </div>
        <button onClick={loadDashboard}>Refresh Dashboard</button>
      </div>

      {loading && <section className="card">Loading dashboard...</section>}

      <div className="grid4">
        <StatCard
          label="Pre-study survey"
          value={surveyStatus.pre ? "Complete" : "Not Done"}
          note={surveyStatus.pre ? "Baseline saved" : "Complete before testing"}
        />
        <StatCard
          label="Available pantry items"
          value={activePantry.length}
          note="Items currently entered"
        />
        <StatCard
          label="Total usable amount"
          value={totalAmount}
          note="Based on saved quantities"
        />
        <StatCard
          label="Post-study survey"
          value={surveyStatus.post ? "Complete" : "Not Done"}
          note={surveyStatus.post ? "Final feedback saved" : "Complete after study use"}
        />
      </div>

      <div className="grid2">
        <section className="card">
          <h2>Pantry Category Breakdown</h2>
          <p className="helperText">
            This chart shows the mix of pantry items by category.
          </p>

          {categoryData.length === 0 ? (
            <p>Add pantry items to see your pantry category breakdown.</p>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={340}>
                <PieChart>
                  <Pie
                    data={categoryData}
                    dataKey="value"
                    nameKey="name"
                    outerRadius={115}
                    label={renderPieLabel}
                    labelLine={false}
                  >
                    {categoryData.map((entry) => (
                      <Cell key={entry.name} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>

              <div className="colorKey">
                {categoryData.map((category) => (
                  <div className="colorKeyItem" key={category.name}>
                    <span
                      className="colorDot"
                      style={{ backgroundColor: category.fill }}
                    ></span>
                    <span>{category.name}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </section>

        <section className="card">
          <h2>Expiration Alerts</h2>
          <p className="helperText">
            Items are grouped by urgency so you can decide what to use first.
          </p>

          {expirationAlerts.length === 0 ? (
            <p>No items expiring within the next 10 days.</p>
          ) : (
            <div className="alertList">
              {expirationAlerts.map((item) => (
                <div className={`alertItem ${item.alert.className}`} key={item.id}>
                  <div>
                    <strong>{item.item_name}</strong>
                    <p>{item.category || "Other"} • {item.quantity} {item.unit}</p>
                  </div>
                  <div>
                    <span>{item.alert.label}</span>
                    <small>{item.alert.detail}</small>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="card">
        <h2>Suggested Grocery List</h2>
        <p className="helperText">
          These are simple grocery suggestions based on common missing items.
          This will become smarter once the full recommendation engine is upgraded.
        </p>

        {grocerySuggestions.length === 0 ? (
          <p>Your pantry already has several common grocery basics entered.</p>
        ) : (
          <div className="groceryGrid">
            {grocerySuggestions.map((item) => (
              <div className="groceryItem" key={item.name}>
                <strong>{item.name}</strong>
                <span>{item.category}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
