import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

const ALLERGY_OPTIONS = [
  "Milk / Dairy",
  "Eggs",
  "Peanuts",
  "Tree nuts",
  "Fish",
  "Shellfish",
  "Wheat / Gluten",
  "Soy",
  "Sesame",
  "Mushrooms",
  "Onions",
  "Other",
];

const AVOID_FOOD_OPTIONS = [
  "Pork",
  "Beef",
  "Chicken",
  "Seafood",
  "Mushrooms",
  "Onions",
  "Spicy foods",
  "High sugar foods",
  "Fried foods",
  "Dairy",
  "Gluten",
  "Processed meat",
  "Other",
];

const MEAL_TYPES = [
  "Breakfast",
  "Lunch",
  "Dinner",
  "Snack",
  "Quick Meal",
  "Brunch",
];

const CUISINES = [
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
  username: "",
  household_size: 1,
  allergies: "",
  dietary_restrictions: "",
  avoid_foods: "",
  preferred_meal_type: "",
  preferred_cuisine: "",
  quick_meals_preferred: true,
  profile_notes: "",
};

function splitValues(value) {
  if (!value) return [];
  return String(value)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinValues(values) {
  return values.join(", ");
}

function toggleValue(currentValues, value) {
  if (currentValues.includes(value)) {
    return currentValues.filter((item) => item !== value);
  }

  return [...currentValues, value];
}

export default function Profile() {
  const user = getUser();

  const [profile, setProfile] = useState({
    ...emptyProfile,
    username: user?.username || "",
  });

  const [allergyChoice, setAllergyChoice] = useState("");
  const [avoidChoice, setAvoidChoice] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const selectedAllergies = useMemo(
    () => splitValues(profile.allergies),
    [profile.allergies]
  );

  const selectedAvoidFoods = useMemo(
    () => splitValues(profile.avoid_foods),
    [profile.avoid_foods]
  );

  const selectedMealTypes = useMemo(
    () => splitValues(profile.preferred_meal_type),
    [profile.preferred_meal_type]
  );

  const selectedCuisines = useMemo(
    () => splitValues(profile.preferred_cuisine),
    [profile.preferred_cuisine]
  );

  useEffect(() => {
    async function loadProfile() {
      try {
        if (api.getProfile) {
          const data = await api.getProfile(user.id);

          if (data) {
            setProfile({
              ...emptyProfile,
              ...data,
              username: data.username || user.username,
              household_size: data.household_size || 1,
              quick_meals_preferred:
                data.quick_meals_preferred === undefined
                  ? true
                  : data.quick_meals_preferred,
            });
          }
        }
      } catch (err) {
        setError(err.message || "Could not load profile.");
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
  }, [user.id, user.username]);

  function change(field, value) {
    setProfile((prev) => ({
      ...prev,
      [field]: value,
    }));
  }

  function addAllergy() {
    if (!allergyChoice) return;

    const updated = toggleValue(selectedAllergies, allergyChoice);
    change("allergies", joinValues(updated));
    setAllergyChoice("");
  }

  function removeAllergy(value) {
    change(
      "allergies",
      joinValues(selectedAllergies.filter((item) => item !== value))
    );
  }

  function addAvoidFood() {
    if (!avoidChoice) return;

    const updated = toggleValue(selectedAvoidFoods, avoidChoice);
    change("avoid_foods", joinValues(updated));
    setAvoidChoice("");
  }

  function removeAvoidFood(value) {
    change(
      "avoid_foods",
      joinValues(selectedAvoidFoods.filter((item) => item !== value))
    );
  }

  function toggleMealType(value) {
    change("preferred_meal_type", joinValues(toggleValue(selectedMealTypes, value)));
  }

  function toggleCuisine(value) {
    change("preferred_cuisine", joinValues(toggleValue(selectedCuisines, value)));
  }

  async function saveProfile(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    const payload = {
      user_id: user.id,
      username: profile.username || user.username,
      household_size: Number(profile.household_size || 1),
      allergies: profile.allergies || "",
      dietary_restrictions: profile.dietary_restrictions || "",
      avoid_foods: profile.avoid_foods || "",
      preferred_meal_type: profile.preferred_meal_type || "",
      preferred_cuisine: profile.preferred_cuisine || "",
      quick_meals_preferred: Boolean(profile.quick_meals_preferred),
      profile_notes: profile.profile_notes || "",
    };

    try {
      if (api.saveProfile) {
        await api.saveProfile(payload);
      } else if (api.updateProfile) {
        await api.updateProfile(user.id, payload);
      } else if (api.createOrUpdateProfile) {
        await api.createOrUpdateProfile(payload);
      } else {
        throw new Error("Profile save function was not found in api/client.js.");
      }

      setMessage("Profile saved.");
    } catch (err) {
      setError(err.message || "Could not save profile.");
    }
  }

  if (loading) {
    return (
      <div className="profilePage">
        <section className="surveyHero profileHero">
          <p className="eyebrow">Smart Pantry Profile</p>
          <h1>Profile & Preferences</h1>
          <p>Loading your profile...</p>
        </section>
      </div>
    );
  }

  return (
    <div className="profilePage">
      <section className="surveyHero profileHero">
        <p className="eyebrow">Smart Pantry Profile</p>
        <h1>Profile & Preferences</h1>
        <p>
          Save food preferences, allergies, household details, and meal choices.
          This helps Smart Pantry recommend meals that make more sense for each participant.
        </p>
      </section>

      <section className="card profileCard">
        <form onSubmit={saveProfile} className="profileForm">
          <div className="profileSection">
            <h2>Household Details</h2>

            <div className="profileGrid">
              <label>
                Username
                <input
                  value={profile.username}
                  onChange={(e) => change("username", e.target.value)}
                  placeholder="Username"
                />
              </label>

              <label>
                Household Size
                <input
                  type="number"
                  min="1"
                  value={profile.household_size}
                  onChange={(e) => change("household_size", e.target.value)}
                />
              </label>

              <label className="profileWide">
                Dietary Restrictions
                <input
                  value={profile.dietary_restrictions}
                  onChange={(e) =>
                    change("dietary_restrictions", e.target.value)
                  }
                  placeholder="Example: no pork, low carb, vegetarian"
                />
              </label>
            </div>
          </div>

          <div className="profileSection">
            <h2>Allergies</h2>
            <p>Select common food allergies from the dropdown.</p>

            <div className="dropdownAddRow">
              <select
                value={allergyChoice}
                onChange={(e) => setAllergyChoice(e.target.value)}
              >
                <option value="">Choose allergy</option>
                {ALLERGY_OPTIONS.map((option) => (
                  <option key={option}>{option}</option>
                ))}
              </select>

              <button type="button" onClick={addAllergy}>
                Add
              </button>
            </div>

            <div className="selectedChipList">
              {selectedAllergies.length === 0 ? (
                <span className="emptyChip">No allergies selected</span>
              ) : (
                selectedAllergies.map((item) => (
                  <button
                    type="button"
                    className="selectedChip"
                    key={item}
                    onClick={() => removeAllergy(item)}
                  >
                    {item} ×
                  </button>
                ))
              )}
            </div>
          </div>

          <div className="profileSection">
            <h2>Foods to Avoid</h2>
            <p>Select foods the participant does not want included in recommendations.</p>

            <div className="dropdownAddRow">
              <select
                value={avoidChoice}
                onChange={(e) => setAvoidChoice(e.target.value)}
              >
                <option value="">Choose food to avoid</option>
                {AVOID_FOOD_OPTIONS.map((option) => (
                  <option key={option}>{option}</option>
                ))}
              </select>

              <button type="button" onClick={addAvoidFood}>
                Add
              </button>
            </div>

            <div className="selectedChipList">
              {selectedAvoidFoods.length === 0 ? (
                <span className="emptyChip">No avoided foods selected</span>
              ) : (
                selectedAvoidFoods.map((item) => (
                  <button
                    type="button"
                    className="selectedChip avoidChip"
                    key={item}
                    onClick={() => removeAvoidFood(item)}
                  >
                    {item} ×
                  </button>
                ))
              )}
            </div>
          </div>

          <div className="profileSection">
            <h2>Preferred Meal Types</h2>

            <div className="buttonChipGrid">
              {MEAL_TYPES.map((mealType) => (
                <button
                  type="button"
                  key={mealType}
                  className={
                    selectedMealTypes.includes(mealType)
                      ? "preferenceChip activePreference"
                      : "preferenceChip"
                  }
                  onClick={() => toggleMealType(mealType)}
                >
                  {mealType}
                </button>
              ))}
            </div>
          </div>

          <div className="profileSection">
            <h2>Preferred Cuisines</h2>

            <div className="buttonChipGrid">
              {CUISINES.map((cuisine) => (
                <button
                  type="button"
                  key={cuisine}
                  className={
                    selectedCuisines.includes(cuisine)
                      ? "preferenceChip activePreference"
                      : "preferenceChip"
                  }
                  onClick={() => toggleCuisine(cuisine)}
                >
                  {cuisine}
                </button>
              ))}
            </div>
          </div>

          <div className="profileSection compactCheckboxSection">
            <label className="quickMealToggle">
              <input
                type="checkbox"
                checked={Boolean(profile.quick_meals_preferred)}
                onChange={(e) =>
                  change("quick_meals_preferred", e.target.checked)
                }
              />
              Prioritize quick, simple meals when possible
            </label>
          </div>

          <div className="profileSection">
            <h2>Extra Notes</h2>

            <textarea
              value={profile.profile_notes}
              onChange={(e) => change("profile_notes", e.target.value)}
              placeholder="Add anything else that should help Smart Pantry make better recommendations..."
            />
          </div>

          <button className="saveProfileButton" type="submit">
            Save Profile
          </button>
        </form>

        {message && <p className="success">{message}</p>}
        {error && <p className="error">{error}</p>}
      </section>
    </div>
  );
}
