import { useEffect, useMemo, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { api } from "../api/client.js";
import StatCard from "../components/StatCard.jsx";

const COLORS = [
  "#2563eb",
  "#16a34a",
  "#f97316",
  "#9333ea",
  "#dc2626",
  "#0891b2",
  "#ca8a04",
  "#ec4899",
];

const GROCERY_IDEAS = [
  {
    item: "Tortillas",
    worksWith: ["chicken", "lettuce", "beans", "rice", "cheese", "eggs", "beef"],
    profileMatches: ["lunch", "dinner", "mexican", "tex-mex"],
  },
  {
    item: "Bread",
    worksWith: ["eggs", "tuna", "chicken", "lettuce", "cheese", "turkey"],
    profileMatches: ["breakfast", "lunch", "american"],
  },
  {
    item: "Cheese",
    worksWith: ["eggs", "chicken", "rice", "pasta", "bread", "tortillas", "beef"],
    profileMatches: ["breakfast", "lunch", "dinner", "american", "mexican"],
  },
  {
    item: "Rice",
    worksWith: ["chicken", "beans", "beef", "fish", "vegetables", "eggs"],
    profileMatches: ["lunch", "dinner", "asian", "mexican", "american"],
  },
  {
    item: "Beans",
    worksWith: ["rice", "chicken", "lettuce", "tortillas", "beef", "cheese"],
    profileMatches: ["lunch", "dinner", "mexican", "tex-mex"],
  },
  {
    item: "Pasta",
    worksWith: ["chicken", "cheese", "vegetables", "beef", "tomatoes"],
    profileMatches: ["dinner", "italian", "american"],
  },
  {
    item: "Pasta sauce",
    worksWith: ["pasta", "chicken", "beef", "cheese", "vegetables"],
    profileMatches: ["dinner", "italian", "american"],
  },
  {
    item: "Tomatoes",
    worksWith: ["lettuce", "chicken", "tortillas", "bread", "beans", "cheese"],
    profileMatches: ["lunch", "dinner", "mexican", "american"],
  },
  {
    item: "Salad dressing",
    worksWith: ["lettuce", "spinach", "chicken", "tuna", "fish"],
    profileMatches: ["lunch", "dinner"],
  },
  {
    item: "Mixed vegetables",
    worksWith: ["chicken", "rice", "pasta", "eggs", "beef"],
    profileMatches: ["lunch", "dinner", "american", "asian"],
  },
  {
    item: "Oats",
    worksWith: ["milk", "yogurt", "fruit", "banana"],
    profileMatches: ["breakfast"],
  },
  {
    item: "Fruit",
    worksWith: ["yogurt", "oats", "cereal", "milk"],
    profileMatches: ["breakfast", "snack"],
  },
];

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

function normalizeText(value) {
  return String(value || "").toLowerCase().trim();
}

function daysUntil(dateString) {
  if (!dateString) return null;

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const exp = new Date(dateString);
  exp.setHours(0, 0, 0, 0);

  return Math.ceil((exp - today) / (1000 * 60 * 60 * 24));
}

function getAlertLabel(days) {
  if (days <= 1) return "Use Immediately!!";
  if (days <= 4) return "Warning Use Soon!";
  return "Plan Ahead";
}

function getAlertClass(days) {
  if (days <= 1) return "danger";
  if (days <= 4) return "warning";
  return "plan";
}

function pantryHasItem(pantryNames, groceryItem) {
  const grocery = normalizeText(groceryItem);

  return pantryNames.some(
    (name) => name.includes(grocery) || grocery.includes(name)
  );
}

function profileText(profile) {
  if (!profile) return "";

  return [
    profile.preferred_meal_type,
    profile.preferred_cuisine,
    profile.profile_notes,
  ]
    .map(normalizeText)
    .join(" ");
}

function getSuggestionLabel(matchCount, profileMatched) {
  if (matchCount >= 3) {
    return { label: "High", className: "high", note: "Strong match with pantry items" };
  }

  if (matchCount === 2) {
    return { label: "Medium", className: "medium", note: "Could help build more meals" };
  }

  if (profileMatched) {
    return { label: "Suggested", className: "suggested", note: "Based on saved preferences" };
  }

  return { label: "Low", className: "low", note: "Optional pantry add-on" };
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0].payload;

  return (
    <div className="pieTooltip">
      <strong>{data.name}</strong>
      <span>{data.value} item(s)</span>
      <small>{data.percent}% of pantry</small>
    </div>
  );
}

function renderPercentLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  const value = percent > 1 ? Math.round(percent) : Math.round(percent * 100);

  if (!value || value < 7) {
    return null;
  }

  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.6;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      fontSize="12"
      fontWeight="900"
    >
      {`${value}%`}
    </text>
  );
}


function renderInsidePercentLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  const value = percent <= 1 ? Math.round(percent * 100) : Math.round(percent);

  if (!value || value < 6) {
    return null;
  }

  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.58;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      fontSize="15"
      fontWeight="950"
    >
      {`${value}%`}
    </text>
  );
}

export default function Dashboard() {
  const user = getUser();
  const customKey = `sp2_custom_grocery_${user.id}`;

  const [pantry, setPantry] = useState([]);
  const [profile, setProfile] = useState(null);
  const [customItem, setCustomItem] = useState("");
  const [customGroceries, setCustomGroceries] = useState([]);
  const [surveyStatus, setSurveyStatus] = useState({ pre: false, post: false });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [pantryData, statusData, profileData] = await Promise.all([
          api.getPantry(user.id),
          api.getSurveyStatus(user.id),
          api.getProfile ? api.getProfile(user.id) : Promise.resolve(null),
        ]);

        setPantry(pantryData || []);
        setSurveyStatus(statusData || { pre: false, post: false });
        setProfile(profileData || null);

        const savedCustomItems = JSON.parse(localStorage.getItem(customKey) || "[]");
        setCustomGroceries(savedCustomItems);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, [user.id, customKey]);

  function addCustomGrocery(e) {
    e.preventDefault();

    const cleaned = customItem.trim();
    if (!cleaned) return;

    const updated = [
      ...customGroceries,
      {
        item: cleaned,
        label: "Custom",
        className: "custom",
        note: "Added by participant",
      },
    ];

    setCustomGroceries(updated);
    localStorage.setItem(customKey, JSON.stringify(updated));
    setCustomItem("");
  }

  function removeCustomGrocery(indexToRemove) {
    const updated = customGroceries.filter((_item, index) => index !== indexToRemove);
    setCustomGroceries(updated);
    localStorage.setItem(customKey, JSON.stringify(updated));
  }

  const categoryData = useMemo(() => {
    const counts = {};

    pantry.forEach((item) => {
      const key = item.category || "Other";
      counts[key] = (counts[key] || 0) + 1;
    });

    const total = Object.values(counts).reduce((sum, value) => sum + value, 0);

    return Object.entries(counts).map(([name, value]) => ({
      name,
      value,
      percent: total > 0 ? Math.round((value / total) * 100) : 0,
    }));
  }, [pantry]);

  const alerts = useMemo(() => {
    return pantry
      .map((item) => ({
        ...item,
        days: daysUntil(item.expiration_date),
      }))
      .filter((item) => item.days !== null && item.days <= 10)
      .sort((a, b) => a.days - b.days);
  }, [pantry]);

  const suggestedGroceries = useMemo(() => {
    const pantryNames = pantry.map((item) => normalizeText(item.item_name));
    const userProfileText = profileText(profile);

    const suggestions = GROCERY_IDEAS.map((idea) => {
      if (pantryHasItem(pantryNames, idea.item)) return null;

      const matchedPantryItems = idea.worksWith.filter((ingredient) =>
        pantryNames.some((name) => name.includes(ingredient))
      );

      const profileMatched = idea.profileMatches.some((preference) =>
        userProfileText.includes(preference)
      );

      if (matchedPantryItems.length === 0 && !profileMatched) return null;

      const status = getSuggestionLabel(matchedPantryItems.length, profileMatched);

      return {
        item: idea.item,
        label: status.label,
        className: status.className,
        note: status.note,
      };
    })
      .filter(Boolean)
      .sort((a, b) => {
        const rank = { High: 1, Medium: 2, Suggested: 3, Low: 4 };
        return rank[a.label] - rank[b.label];
      })
      .slice(0, 6);

    return suggestions;
  }, [pantry, profile]);

  const totalAmount = pantry.reduce(
    (sum, item) => sum + Number(item.quantity || 0),
    0
  );

  const completedSteps = [
    surveyStatus.pre,
    pantry.length > 0,
    surveyStatus.post,
  ].filter(Boolean).length;

  if (loading) {
    return (
      <div>
        <section className="dashboardHero">
          <h1>Dashboard</h1>
          <p>Loading your Smart Pantry dashboard...</p>
        </section>
      </div>
    );
  }

  return (
    <div className="dashboardPage">
      <section className="dashboardHero">
        <div>
          <p className="eyebrow">Welcome back, {user.username}</p>
          <h1>Smart Pantry Dashboard</h1>
          <p>
            Use this dashboard to complete study steps, track pantry items via
            expiration alerts, and find meal ideas based on the food you already
            have. Let&apos;s get started.
          </p>
        </div>

        <div className="heroProgressBubble">
          <strong>{completedSteps}/3</strong>
          <span>Study steps started</span>
        </div>
      </section>

      <section className="expirationBanner">
        <div className="expirationBannerHeader">
          <div>
            <h2>Expiration Alerts</h2>
            <p>Items that may need attention within the next 10 days.</p>
          </div>
          <span>{alerts.length} alert(s)</span>
        </div>

        {alerts.length === 0 ? (
          <div className="expirationEmpty">
            No pantry items are expiring within 10 days.
          </div>
        ) : (
          <div className="expirationBannerList">
            {alerts.map((item) => (
              <div
                className={`expirationPill ${getAlertClass(item.days)}`}
                key={item.id}
              >
                <strong>{item.item_name}</strong>
                <span>{getAlertLabel(item.days)}</span>
                <small>
                  {item.days < 0
                    ? `${Math.abs(item.days)} day(s) expired`
                    : `${item.days} day(s) left`}
                </small>
              </div>
            ))}
          </div>
        )}
      </section>

      <div className="compactStatsGrid">
        <StatCard
          label="Pre-study survey"
          value={surveyStatus.pre ? "Complete" : "Not Done"}
        />
        <StatCard label="Pantry items" value={pantry.length} />
        <StatCard label="Total usable amount" value={totalAmount} />
        <StatCard
          label="Post-study survey"
          value={surveyStatus.post ? "Complete" : "Not Done"}
        />
      </div>

      <div className="dashboardGrid compactDashboardGrid">
        <section className="card dashboardCard pantryChartCard">
          <h2>Pantry Category Breakdown</h2>

          {categoryData.length === 0 ? (
            <p>No pantry items have been added yet.</p>
          ) : (
            <>
              <div className="pieAndLegendLayout">
                <div className="largePieWrap">
                  <ResponsiveContainer width="100%" height={320}>
                    <PieChart margin={{ top: 18, right: 18, bottom: 18, left: 18 }}>
                      <Pie
                        data={categoryData}
                        dataKey="value"
                        nameKey="name"
                        outerRadius={120}
                        labelLine={false}
                        label={renderInsidePercentLabel}
                      >
                        {categoryData.map((_entry, index) => (
                          <Cell key={index} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="legendSideBox">
                  <h3>Breakdown Table</h3>

                  <div className="categoryLegend sideLegend">
                    {categoryData.map((entry, index) => (
                      <div className="legendItem" key={entry.name}>
                        <span
                          className="legendDot"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <strong>{entry.name}</strong>
                        <small>{entry.value} item(s)</small>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </section>

        <section className="card dashboardCard suggestedGroceryCard compactGroceryCard">
          <h2>Suggested Grocery List</h2>
          <p className="groceryListNote">
            Suggested items can help create more meals from what is already in the pantry.
          </p>

          <form className="customGroceryForm" onSubmit={addCustomGrocery}>
            <input
              value={customItem}
              onChange={(e) => setCustomItem(e.target.value)}
              placeholder="Add your own grocery item..."
            />
            <button type="submit">Add</button>
          </form>

          {suggestedGroceries.length === 0 && customGroceries.length === 0 ? (
            <div className="groceryEmpty">
              Add more pantry items or profile preferences to receive grocery suggestions.
            </div>
          ) : (
            <div className="compactGroceryList">
              {suggestedGroceries.map((suggestion, index) => (
                <div
                  className={`compactGroceryItem priority-${suggestion.className}`}
                  key={`${suggestion.item}-${index}`}
                >
                  <span className="groceryColorDot"></span>

                  <div className="groceryIngredientText">
                    <strong>{suggestion.item}</strong>
                    <span>{suggestion.note}</span>
                  </div>

                  <small>{suggestion.label}</small>
                </div>
              ))}

              {customGroceries.map((item, index) => (
                <div
                  className="compactGroceryItem priority-custom"
                  key={`custom-${item.item}-${index}`}
                >
                  <span className="groceryColorDot"></span>

                  <div className="groceryIngredientText">
                    <strong>{item.item}</strong>
                    <span>{item.note}</span>
                  </div>

                  <button
                    type="button"
                    className="removeGroceryButton"
                    onClick={() => removeCustomGrocery(index)}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
