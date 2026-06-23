import { useEffect, useState } from "react";
import { api } from "../api/client.js";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

const CATEGORY_OPTIONS = [
  "Protein",
  "Dairy",
  "Grain",
  "Fruit",
  "Vegetable",
  "Canned Goods",
  "Frozen",
  "Snack",
  "Condiment",
  "Beverage",
  "Other",
];

const UNIT_OPTIONS = [
  "item",
  "items",
  "serving",
  "servings",
  "piece",
  "pieces",
  "cup",
  "cups",
  "oz",
  "lb",
  "lbs",
  "pound",
  "pounds",
  "grams",
  "kg",
  "can",
  "cans",
  "box",
  "boxes",
  "bag",
  "bags",
  "bottle",
  "bottles",
  "carton",
  "cartons",
  "bunch",
  "dozen",
  "slice",
  "slices",
];

const CONTAINER_OPTIONS = [
  "",
  "bag",
  "bag/can",
  "bag/box",
  "box",
  "can",
  "bottle",
  "bottle/jar",
  "jar",
  "carton",
  "package",
  "container",
  "tub",
  "tray",
  "pouch",
  "loaf",
  "bunch",
  "dozen",
  "none",
];

const emptyForm = {
  item_name: "",
  category: "Other",
  quantity: 1,
  unit: "item",
  container_type: "",
  expiration_date: "",
  barcode: "",
  brand: "",
  source: "",
  notes: "",
};

function cleanDate(value) {
  if (!value) return "";
  return String(value).slice(0, 10);
}

function normalizeItem(item) {
  return {
    ...item,
    item_name: item.item_name || "",
    category: item.category || "Other",
    quantity: item.quantity ?? 1,
    unit: item.unit || "item",
    container_type: item.container_type || "",
    expiration_date: cleanDate(item.expiration_date),
    barcode: item.barcode || "",
    brand: item.brand || "",
    source: item.source || "",
    notes: item.notes || "",
  };
}

function friendlyFetchError(err) {
  if (String(err.message || "").toLowerCase().includes("failed to fetch")) {
    return "Failed to fetch. Make sure the backend terminal is running at http://127.0.0.1:8000.";
  }

  return err.message || "Something went wrong.";
}

export default function Pantry() {
  const user = getUser();

  const [items, setItems] = useState([]);
  const [editedItems, setEditedItems] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [barcodeSearch, setBarcodeSearch] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [barcodeLoading, setBarcodeLoading] = useState(false);

  async function load() {
    try {
      setLoading(true);
      const data = await api.getPantry(user.id);
      const normalized = (data || []).map(normalizeItem);
      setItems(normalized);
      setEditedItems(normalized);
    } catch (err) {
      setError(friendlyFetchError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function change(field, value) {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }));
  }

  function changeTable(rowIndex, field, value) {
    setEditedItems((prev) =>
      prev.map((item, index) =>
        index === rowIndex
          ? {
              ...item,
              [field]: value,
            }
          : item
      )
    );
  }

  async function lookupBarcode(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    const barcode = barcodeSearch.trim();
    if (!barcode) {
      setError("Enter a barcode or UPC first.");
      return;
    }

    setBarcodeLoading(true);

    try {
      const possiblePaths = [
        `/barcodes/lookup/${barcode}`,
        `/barcodes/${barcode}`,
        `/barcode/lookup/${barcode}`,
      ];

      let data = null;

      for (const path of possiblePaths) {
        try {
          const response = await fetch(`${API_URL}${path}`);

          if (response.ok) {
            data = await response.json();
            break;
          }
        } catch {
          // try next path
        }
      }

      if (!data) {
        setError("No barcode match found. You can still enter the item manually.");
        return;
      }

      const product = data.item || data.product || data.data || data;

      const itemName =
        product.item_name ||
        product.product_name ||
        product.name ||
        product.description ||
        product.food_name ||
        "";

      const brand = product.brand || product.brands || product.brand_name || "";
      const category =
        product.category ||
        product.food_category ||
        product.main_category ||
        "Other";

      setForm((prev) => ({
        ...prev,
        item_name: itemName || prev.item_name,
        brand: brand || prev.brand,
        barcode,
        category: CATEGORY_OPTIONS.includes(category) ? category : prev.category,
        source: "barcode_lookup",
        notes: prev.notes || "Found by barcode lookup",
      }));

      setMessage(
        itemName
          ? `Barcode found: ${itemName}`
          : "Barcode found. Review the item details before adding."
      );
    } catch (err) {
      setError(friendlyFetchError(err));
    } finally {
      setBarcodeLoading(false);
    }
  }

  async function addItem(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    try {
      await api.addPantryItem({
        ...form,
        user_id: user.id,
        quantity: Number(form.quantity || 0),
      });

      setForm(emptyForm);
      setBarcodeSearch("");
      setMessage("Pantry item added.");
      await load();
    } catch (err) {
      setError(friendlyFetchError(err));
    }
  }

  async function saveRow(item) {
    setMessage("");
    setError("");

    try {
      await api.updatePantryItem(item.id, {
        item_name: item.item_name,
        category: item.category,
        quantity: Number(item.quantity || 0),
        unit: item.unit,
        container_type: item.container_type,
        expiration_date: item.expiration_date,
        barcode: item.barcode,
        brand: item.brand,
        source: item.source,
        notes: item.notes,
      });

      setMessage("Pantry item updated.");
      await load();
    } catch (err) {
      setError(friendlyFetchError(err));
    }
  }

  async function remove(id) {
    setMessage("");
    setError("");

    try {
      await api.deletePantryItem(id);
      setMessage("Pantry item deleted.");
      await load();
    } catch (err) {
      setError(friendlyFetchError(err));
    }
  }

  function resetRow(rowIndex) {
    setEditedItems((prev) =>
      prev.map((item, index) => (index === rowIndex ? items[rowIndex] : item))
    );
  }

  return (
    <div className="pantryPage">
      <section className="surveyHero">
        <p className="eyebrow">Smart Pantry Inventory</p>
        <h1>My Pantry</h1>
        <p>
          Add pantry items manually or search by barcode. Edit directly in the table
          if something was entered wrong.
        </p>
      </section>

      <section className="card pantryFormCard">
        <h2>Add Pantry Item</h2>

        <form className="barcodeLookupBar" onSubmit={lookupBarcode}>
          <input
            value={barcodeSearch}
            onChange={(e) => setBarcodeSearch(e.target.value)}
            placeholder="Search by barcode / UPC"
          />
          <button type="submit" disabled={barcodeLoading}>
            {barcodeLoading ? "Searching..." : "Search UPC"}
          </button>
        </form>

        <form className="formGrid pantryAddGrid" onSubmit={addItem}>
          <input
            placeholder="Item name"
            value={form.item_name}
            onChange={(e) => change("item_name", e.target.value)}
            required
          />

          <select
            value={form.category}
            onChange={(e) => change("category", e.target.value)}
          >
            {CATEGORY_OPTIONS.map((category) => (
              <option key={category}>{category}</option>
            ))}
          </select>

          <input
            type="number"
            step="0.1"
            min="0"
            placeholder="Quantity"
            value={form.quantity}
            onChange={(e) => change("quantity", e.target.value)}
          />

          <select value={form.unit} onChange={(e) => change("unit", e.target.value)}>
            {UNIT_OPTIONS.map((unit) => (
              <option key={unit}>{unit}</option>
            ))}
          </select>

          <select
            value={form.container_type}
            onChange={(e) => change("container_type", e.target.value)}
          >
            <option value="">Container type</option>
            {CONTAINER_OPTIONS.filter(Boolean).map((container) => (
              <option key={container}>{container}</option>
            ))}
          </select>

          <input
            type="date"
            value={form.expiration_date}
            onChange={(e) => change("expiration_date", e.target.value)}
          />

          <input
            placeholder="Barcode / UPC"
            value={form.barcode}
            onChange={(e) => change("barcode", e.target.value)}
          />

          <input
            placeholder="Brand"
            value={form.brand}
            onChange={(e) => change("brand", e.target.value)}
          />

          <input
            className="wideInput"
            placeholder="Notes"
            value={form.notes}
            onChange={(e) => change("notes", e.target.value)}
          />

          <button>Add Item</button>
        </form>

        {message && <p className="success">{message}</p>}
        {error && <p className="error">{error}</p>}
      </section>

      <section className="card pantryTableCard">
        <div className="pantrySectionHeader">
          <div>
            <h2>Current Pantry</h2>
            <p>Edit directly in the table, then click Save on that row.</p>
          </div>

          <span>{editedItems.length} item(s)</span>
        </div>

        {loading ? (
          <p>Loading pantry items...</p>
        ) : editedItems.length === 0 ? (
          <div className="groceryEmpty">No pantry items have been added yet.</div>
        ) : (
          <div className="realTableWrap">
            <table className="realPantryTable">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Category</th>
                  <th>Qty</th>
                  <th>Unit</th>
                  <th>Container</th>
                  <th>Expiration</th>
                  <th>Brand</th>
                  <th>UPC</th>
                  <th>Notes</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {editedItems.map((item, rowIndex) => (
                  <tr key={item.id}>
                    <td>
                      <input
                        value={item.item_name}
                        onChange={(e) =>
                          changeTable(rowIndex, "item_name", e.target.value)
                        }
                      />
                    </td>

                    <td>
                      <select
                        value={item.category}
                        onChange={(e) =>
                          changeTable(rowIndex, "category", e.target.value)
                        }
                      >
                        {CATEGORY_OPTIONS.map((category) => (
                          <option key={category}>{category}</option>
                        ))}
                      </select>
                    </td>

                    <td>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        value={item.quantity}
                        onChange={(e) =>
                          changeTable(rowIndex, "quantity", e.target.value)
                        }
                      />
                    </td>

                    <td>
                      <select
                        value={item.unit}
                        onChange={(e) =>
                          changeTable(rowIndex, "unit", e.target.value)
                        }
                      >
                        {UNIT_OPTIONS.map((unit) => (
                          <option key={unit}>{unit}</option>
                        ))}
                      </select>
                    </td>

                    <td>
                      <select
                        value={item.container_type}
                        onChange={(e) =>
                          changeTable(rowIndex, "container_type", e.target.value)
                        }
                      >
                        {CONTAINER_OPTIONS.map((container) => (
                          <option key={container} value={container}>
                            {container || "none"}
                          </option>
                        ))}
                      </select>
                    </td>

                    <td>
                      <input
                        type="date"
                        value={item.expiration_date}
                        onChange={(e) =>
                          changeTable(rowIndex, "expiration_date", e.target.value)
                        }
                      />
                    </td>

                    <td>
                      <input
                        value={item.brand}
                        onChange={(e) =>
                          changeTable(rowIndex, "brand", e.target.value)
                        }
                      />
                    </td>

                    <td>
                      <input
                        value={item.barcode}
                        onChange={(e) =>
                          changeTable(rowIndex, "barcode", e.target.value)
                        }
                      />
                    </td>

                    <td>
                      <input
                        value={item.notes}
                        onChange={(e) =>
                          changeTable(rowIndex, "notes", e.target.value)
                        }
                      />
                    </td>

                    <td>
                      <div className="realTableActions">
                        <button
                          type="button"
                          className="miniSave"
                          onClick={() => saveRow(item)}
                        >
                          Save
                        </button>

                        <button
                          type="button"
                          className="miniReset"
                          onClick={() => resetRow(rowIndex)}
                        >
                          Reset
                        </button>

                        <button
                          type="button"
                          className="miniDelete"
                          onClick={() => remove(item.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
