import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { api } from "../api/client.js";

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
  const navigate = useNavigate();
  const user = getUser();
  const customKey = `sp2_custom_grocery_${user.id}`;

  const [pantry, setPantry] = useState([]);
  const [profile, setProfile] = useState(null);
  const [customItem, setCustomItem] = useState("");
  const [customGroceries, setCustomGroceries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [pantryData, profileData] = await Promise.all([
          api.getPantry(user.id),
          api.getProfile ? api.getProfile(user.id) : Promise.resolve(null),
        ]);

        setPantry(pantryData || []);
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

  const categoryCount = categoryData.length;
  const urgentCount = alerts.filter((item) => item.days <= 4).length;

  const nextAction = pantry.length === 0
    ? {
        title: "Add your first pantry items",
        text: "Start with the foods you use most often. Include the quantity, unit, category, and expiration date when available.",
        button: "Go to My Pantry",
        path: "/pantry",
      }
    : urgentCount > 0
      ? {
          title: "Use expiring items first",
          text: `You have ${urgentCount} item${urgentCount === 1 ? "" : "s"} that should be used soon. Review the alerts below before planning your next meal.`,
          button: "Find Meal Ideas",
          path: "/recommendations",
        }
      : {
          title: "Build a meal from your pantry",
          text: "Your pantry is ready. Generate meal ideas based on the ingredients and preferences you have saved.",
          button: "View Recommendations",
          path: "/recommendations",
        };

  if (loading) {
    return (
      <div className="m8DashboardPage">
        <section className="m8DashboardHero m8DashboardLoading">
          <div>
            <p className="m8DashboardEyebrow">Smart Pantry</p>
            <h1>Loading your dashboard...</h1>
            <p>Gathering your pantry totals, expiration alerts, and grocery suggestions.</p>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="m8DashboardPage">
      <section className="m8DashboardHero">
        <div className="m8DashboardHeroCopy">
          <p className="m8DashboardEyebrow">Welcome back, {user.username}</p>
          <h1>Your Smart Pantry overview</h1>
          <p>
            See what is in your pantry, check which items need attention, and decide
            what to do next without searching through every page.
          </p>

          <div className="m8DashboardHeroActions">
            <button type="button" onClick={() => navigate("/pantry")}>
              Manage Pantry
            </button>
            <button
              type="button"
              className="m8DashboardSecondaryButton"
              onClick={() => navigate("/recommendations")}
            >
              Find Meal Ideas
            </button>
          </div>
        </div>

        <aside className="m8NextActionCard" aria-label="Recommended next action">
          <span>Recommended next step</span>
          <h2>{nextAction.title}</h2>
          <p>{nextAction.text}</p>
          <button type="button" onClick={() => navigate(nextAction.path)}>
            {nextAction.button}
          </button>
        </aside>
      </section>

      <section className="m8DashboardStats" aria-label="Pantry summary">
        <article className="m8DashboardStatCard">
          <span className="m8DashboardStatIcon" aria-hidden="true">▦</span>
          <div>
            <p>Pantry items</p>
            <strong>{pantry.length}</strong>
            <small>Different items saved</small>
          </div>
        </article>

        <article className="m8DashboardStatCard">
          <span className="m8DashboardStatIcon" aria-hidden="true">#</span>
          <div>
            <p>Total quantity</p>
            <strong>{Number.isInteger(totalAmount) ? totalAmount : totalAmount.toFixed(1)}</strong>
            <small>Combined usable amount</small>
          </div>
        </article>

        <article className="m8DashboardStatCard">
          <span className="m8DashboardStatIcon" aria-hidden="true">!</span>
          <div>
            <p>Expiring within 10 days</p>
            <strong>{alerts.length}</strong>
            <small>{urgentCount} need attention soon</small>
          </div>
        </article>

        <article className="m8DashboardStatCard">
          <span className="m8DashboardStatIcon" aria-hidden="true">◫</span>
          <div>
            <p>Food categories</p>
            <strong>{categoryCount}</strong>
            <small>Categories represented</small>
          </div>
        </article>
      </section>

      <section className="m8DashboardPanel m8ExpirationPanel">
        <header className="m8DashboardSectionHeader">
          <div>
            <p className="m8DashboardSectionLabel">Expiration check</p>
            <h2>Items that need attention</h2>
            <p>
              These items expire within the next 10 days. Start with the earliest
              date when deciding what to use.
            </p>
          </div>
          <span className="m8DashboardCountBadge">{alerts.length} alert{alerts.length === 1 ? "" : "s"}</span>
        </header>

        {alerts.length === 0 ? (
          <div className="m8DashboardEmptyState">
            <strong>No upcoming expiration alerts</strong>
            <p>Nothing in your pantry is currently marked to expire within 10 days.</p>
          </div>
        ) : (
          <div className="m8ExpirationGrid">
            {alerts.map((item) => (
              <article
                className={`m8ExpirationItem ${getAlertClass(item.days)}`}
                key={item.id}
              >
                <div>
                  <strong>{item.item_name}</strong>
                  <span>{getAlertLabel(item.days)}</span>
                </div>
                <small>
                  {item.days < 0
                    ? `Expired ${Math.abs(item.days)} day${Math.abs(item.days) === 1 ? "" : "s"} ago`
                    : item.days === 0
                      ? "Expires today"
                      : `${item.days} day${item.days === 1 ? "" : "s"} left`}
                </small>
              </article>
            ))}
          </div>
        )}
      </section>

      <div className="m8DashboardMainGrid">
        <section className="m8DashboardPanel m8CategoryPanel">
          <header className="m8DashboardSectionHeader compact">
            <div>
              <p className="m8DashboardSectionLabel">Pantry balance</p>
              <h2>Category breakdown</h2>
              <p>See how your saved pantry items are distributed by food category.</p>
            </div>
          </header>

          {categoryData.length === 0 ? (
            <div className="m8DashboardEmptyState">
              <strong>No category information yet</strong>
              <p>Add pantry items to create your category chart.</p>
              <button type="button" onClick={() => navigate("/pantry")}>Add Pantry Items</button>
            </div>
          ) : (
            <div className="m8CategoryContent">
              <div className="m8PieWrap">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart margin={{ top: 12, right: 12, bottom: 12, left: 12 }}>
                    <Pie
                      data={categoryData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={58}
                      outerRadius={112}
                      paddingAngle={2}
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
                <div className="m8PieCenter" aria-hidden="true">
                  <strong>{pantry.length}</strong>
                  <span>items</span>
                </div>
              </div>

              <div className="m8CategoryLegend">
                {categoryData.map((entry, index) => (
                  <div className="m8CategoryLegendItem" key={entry.name}>
                    <span
                      className="m8CategoryDot"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <div>
                      <strong>{entry.name}</strong>
                      <small>{entry.value} item{entry.value === 1 ? "" : "s"}</small>
                    </div>
                    <b>{entry.percent}%</b>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        <section className="m8DashboardPanel m8GroceryPanel">
          <header className="m8DashboardSectionHeader compact">
            <div>
              <p className="m8DashboardSectionLabel">Optional additions</p>
              <h2>Suggested grocery list</h2>
              <p>
                These suggestions may pair with foods already in your pantry. They
                are ideas, not required purchases.
              </p>
            </div>
          </header>

          <form className="m8GroceryForm" onSubmit={addCustomGrocery}>
            <label htmlFor="dashboard-grocery-item">Add your own item</label>
            <div>
              <input
                id="dashboard-grocery-item"
                value={customItem}
                onChange={(e) => setCustomItem(e.target.value)}
                placeholder="Example: whole-grain bread"
              />
              <button type="submit">Add</button>
            </div>
          </form>

          {suggestedGroceries.length === 0 && customGroceries.length === 0 ? (
            <div className="m8DashboardEmptyState compact">
              <strong>No suggestions yet</strong>
              <p>Add more pantry items or save your meal preferences to receive ideas.</p>
              <button type="button" onClick={() => navigate("/profile")}>Review Preferences</button>
            </div>
          ) : (
            <div className="m8GroceryList">
              {suggestedGroceries.map((suggestion, index) => (
                <article
                  className={`m8GroceryItem priority-${suggestion.className}`}
                  key={`${suggestion.item}-${index}`}
                >
                  <span className="m8GroceryPriorityDot" aria-hidden="true" />
                  <div>
                    <strong>{suggestion.item}</strong>
                    <small>{suggestion.note}</small>
                  </div>
                  <b>{suggestion.label}</b>
                </article>
              ))}

              {customGroceries.map((item, index) => (
                <article className="m8GroceryItem priority-custom" key={`custom-${item.item}-${index}`}>
                  <span className="m8GroceryPriorityDot" aria-hidden="true" />
                  <div>
                    <strong>{item.item}</strong>
                    <small>{item.note}</small>
                  </div>
                  <button type="button" onClick={() => removeCustomGrocery(index)}>Remove</button>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="m8DashboardHowTo" aria-label="How to use Smart Pantry">
        <header>
          <p className="m8DashboardSectionLabel">How to use this app</p>
          <h2>Three simple steps</h2>
        </header>
        <div>
          <article>
            <span>1</span>
            <h3>Keep your pantry current</h3>
            <p>Add new foods and update quantities or expiration dates when something changes.</p>
          </article>
          <article>
            <span>2</span>
            <h3>Review items that expire soon</h3>
            <p>Use the expiration section to decide which ingredients should be prioritized first.</p>
          </article>
          <article>
            <span>3</span>
            <h3>Choose a meal idea</h3>
            <p>Open Meal Recommendations to find options based on your pantry and saved preferences.</p>
          </article>
        </div>
      </section>
    </div>
  );
}
