import { useEffect, useState } from "react";
import { api } from "../api/client.js";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

const mealTypeOptions = [
  "Breakfast",
  "Lunch",
  "Dinner",
  "Snack",
  "Quick Meal",
  "Brunch",
];

const cuisineOptions = [
  "American",
  "Mexican",
  "Italian",
  "Asian",
  "Mediterranean",
  "Everyday",
  "Southern",
  "Comfort Food",
  "Seafood",
];

const emptyProfile = {
  household_size: 1,
  allergies: "",
  dietary_restrictions: "",
  preferred_meal_type: [],
  preferred_cuisine: [],
  avoid_foods: "",
  quick_meals_preferred: true,
  profile_notes: "",
};

function splitList(value) {
  if (!value) return [];

  if (Array.isArray(value)) return value;

  return String(value)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinList(value) {
  if (!value) return "";

  if (Array.isArray(value)) {
    return value.join(", ");
  }

  return String(value);
}

function MultiSelectGroup({ label, options, selected, onChange }) {
  function toggle(option) {
    if (selected.includes(option)) {
      onChange(selected.filter((item) => item !== option));
    } else {
      onChange([...selected, option]);
    }
  }

  return (
    <div className="profileFull">
      <label>{label}</label>
      <div className="multiSelectGrid">
        {options.map((option) => (
          <button
            type="button"
            key={option}
            className={selected.includes(option) ? "multiSelectActive" : "multiSelectButton"}
            onClick={() => toggle(option)}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function Profile() {
  const user = getUser();
  const [profile, setProfile] = useState(emptyProfile);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadProfile() {
    setMessage("");
    setError("");

    try {
      const data = await api.getProfile(user.id);

      setProfile({
        household_size: data.household_size || 1,
        allergies: data.allergies || "",
        dietary_restrictions: data.dietary_restrictions || "",
        preferred_meal_type: splitList(data.preferred_meal_type),
        preferred_cuisine: splitList(data.preferred_cuisine),
        avoid_foods: data.avoid_foods || "",
        quick_meals_preferred:
          data.quick_meals_preferred === false ? false : true,
        profile_notes: data.profile_notes || "",
      });
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadProfile();
  }, [user.id]);

  function change(field, value) {
    setProfile((prev) => ({
      ...prev,
      [field]: value,
    }));
  }

  async function saveProfile(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    try {
      await api.updateProfile(user.id, {
        household_size: Number(profile.household_size || 1),
        allergies: profile.allergies,
        dietary_restrictions: profile.dietary_restrictions,
        preferred_meal_type: joinList(profile.preferred_meal_type),
        preferred_cuisine: joinList(profile.preferred_cuisine),
        avoid_foods: profile.avoid_foods,
        quick_meals_preferred: profile.quick_meals_preferred,
        profile_notes: profile.profile_notes,
      });

      setMessage("Profile and preferences saved.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <div className="pageHeader">
        <h1>Profile & Preferences</h1>
        <p>
          Save food preferences, allergies, and household details. This helps Smart Pantry
          recommend meals that make more sense for each participant.
        </p>
      </div>

      <section className="card">
        <form className="profileForm" onSubmit={saveProfile}>
          <div>
            <label>Username</label>
            <input value={user.username} disabled />
          </div>

          <div>
            <label>Household Size</label>
            <input
              type="number"
              min="1"
              value={profile.household_size}
              onChange={(e) => change("household_size", e.target.value)}
            />
          </div>

          <div>
            <label>Allergies</label>
            <input
              placeholder="Example: onions, mushrooms"
              value={profile.allergies}
              onChange={(e) => change("allergies", e.target.value)}
            />
          </div>

          <div>
            <label>Foods to Avoid</label>
            <input
              placeholder="Example: pork, mushrooms, onions"
              value={profile.avoid_foods}
              onChange={(e) => change("avoid_foods", e.target.value)}
            />
          </div>

          <div className="profileFull">
            <label>Dietary Restrictions</label>
            <input
              placeholder="Example: no pork, low carb, vegetarian"
              value={profile.dietary_restrictions}
              onChange={(e) => change("dietary_restrictions", e.target.value)}
            />
          </div>

          <MultiSelectGroup
            label="Preferred Meal Types"
            options={mealTypeOptions}
            selected={profile.preferred_meal_type}
            onChange={(value) => change("preferred_meal_type", value)}
          />

          <MultiSelectGroup
            label="Preferred Cuisines"
            options={cuisineOptions}
            selected={profile.preferred_cuisine}
            onChange={(value) => change("preferred_cuisine", value)}
          />

          <div className="checkboxLine profileFull">
            <input
              type="checkbox"
              checked={profile.quick_meals_preferred}
              onChange={(e) => change("quick_meals_preferred", e.target.checked)}
            />
            <span>Prioritize quick, simple meals when possible</span>
          </div>

          <div className="profileFull">
            <label>Extra Notes</label>
            <textarea
              placeholder="Add anything else that should help recommendations make more sense."
              value={profile.profile_notes}
              onChange={(e) => change("profile_notes", e.target.value)}
            />
          </div>

          <button type="submit">Save Profile</button>
        </form>

        {message && <p className="success">{message}</p>}
        {error && <p className="error">{error}</p>}
      </section>
    </div>
  );
}
