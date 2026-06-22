import { useEffect, useState } from "react";
import { api } from "../api/client.js";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

const emptyForm = {
  barcode: "",
  item_name: "",
  category: "Other",
  quantity: 1,
  unit: "item",
  container_type: "",
  expiration_date: "",
  brand: "",
  source: "",
  notes: "",
};

const categories = [
  "Protein",
  "Dairy",
  "Grain",
  "Fruit",
  "Vegetable",
  "Canned Goods",
  "Frozen",
  "Snack",
  "Condiment",
  "Tea & Coffee",
  "Other",
];

export default function Pantry() {
  const user = getUser();
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [searchText, setSearchText] = useState("");
  const [searchResults, setSearchResults] = useState([]);

  async function load() {
    const data = await api.getPantry(user.id);
    setItems(data);
  }

  useEffect(() => {
    load();
  }, []);

  function change(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function fillFormFromLookup(item) {
    setForm((prev) => ({
      ...prev,
      barcode: item.barcode || prev.barcode || "",
      item_name: item.item_name || "",
      category: item.category || "Other",
      quantity: Number(item.quantity || 1),
      unit: item.unit || "item",
      container_type: item.container_type || "",
      brand: item.brand || "",
      source: item.source || "barcode_lookup.csv",
    }));
  }

  async function lookupBarcode() {
    setMessage("");
    setError("");

    if (!form.barcode.trim()) {
      setError("Enter a barcode or UPC first.");
      return;
    }

    try {
      const item = await api.lookupBarcode(form.barcode.trim());
      fillFormFromLookup(item);
      setMessage("Barcode found. Review the item details before saving.");
    } catch (err) {
      setError("Barcode not found. You can still enter the item manually.");
    }
  }

  async function searchItems() {
    setMessage("");
    setError("");

    if (!searchText.trim()) {
      setError("Type an item name to search.");
      return;
    }

    try {
      const results = await api.searchBarcodeItems(searchText.trim());
      setSearchResults(results);
      if (results.length === 0) {
        setMessage("No matching items found. You can still enter the item manually.");
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function addItem(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!form.item_name.trim()) {
      setError("Item name is required.");
      return;
    }

    try {
      await api.addPantryItem({
        ...form,
        user_id: user.id,
        quantity: Number(form.quantity || 1),
      });

      setForm(emptyForm);
      setSearchText("");
      setSearchResults([]);
      setMessage("Pantry item added.");
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function remove(id) {
    await api.deletePantryItem(id);
    load();
  }

  return (
    <div>
      <div className="pageHeader">
        <h1>My Pantry</h1>
        <p>Add pantry items manually, by item search, or by barcode/UPC lookup.</p>
      </div>

      <section className="card">
        <h2>Barcode or Item Lookup</h2>
        <p className="helperText">
          Barcode lookup is optional. You can use it to autofill an item, or you can type the item manually.
        </p>

        <div className="lookupGrid">
          <div>
            <label>Barcode / UPC</label>
            <input
              placeholder="Enter barcode or UPC"
              value={form.barcode}
              onChange={(e) => change("barcode", e.target.value)}
            />
          </div>
          <button type="button" onClick={lookupBarcode}>
            Lookup Barcode
          </button>
        </div>

        <div className="lookupGrid">
          <div>
            <label>Search Common Items</label>
            <input
              placeholder="Example: milk, eggs, rice"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </div>
          <button type="button" onClick={searchItems}>
            Search Item
          </button>
        </div>

        {searchResults.length > 0 && (
          <div className="searchResults">
            {searchResults.map((item) => (
              <button
                type="button"
                className="searchResultButton"
                key={`${item.barcode}-${item.item_name}`}
                onClick={() => fillFormFromLookup(item)}
              >
                <strong>{item.item_name}</strong>
                <span>{item.category} {item.brand ? `• ${item.brand}` : ""}</span>
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="card">
        <h2>Add Pantry Item</h2>

        <form className="pantryForm" onSubmit={addItem}>
          <div>
            <label>Item Name</label>
            <input
              placeholder="Item name"
              value={form.item_name}
              onChange={(e) => change("item_name", e.target.value)}
            />
          </div>

          <div>
            <label>Category</label>
            <select value={form.category} onChange={(e) => change("category", e.target.value)}>
              {categories.map((category) => (
                <option key={category}>{category}</option>
              ))}
            </select>
          </div>

          <div>
            <label>Quantity</label>
            <input
              type="number"
              step="0.1"
              value={form.quantity}
              onChange={(e) => change("quantity", e.target.value)}
            />
          </div>

          <div>
            <label>Unit</label>
            <input
              placeholder="item, serving, oz, slices"
              value={form.unit}
              onChange={(e) => change("unit", e.target.value)}
            />
          </div>

          <div>
            <label>Container Type</label>
            <input
              placeholder="carton, can, bag, box"
              value={form.container_type}
              onChange={(e) => change("container_type", e.target.value)}
            />
          </div>

          <div>
            <label>Expiration Date</label>
            <input
              type="date"
              value={form.expiration_date}
              onChange={(e) => change("expiration_date", e.target.value)}
            />
          </div>

          <div>
            <label>Brand</label>
            <input
              placeholder="Optional"
              value={form.brand}
              onChange={(e) => change("brand", e.target.value)}
            />
          </div>

          <div>
            <label>Notes</label>
            <input
              placeholder="Optional notes"
              value={form.notes}
              onChange={(e) => change("notes", e.target.value)}
            />
          </div>

          <button>Add Item</button>
        </form>

        {message && <p className="success">{message}</p>}
        {error && <p className="error">{error}</p>}
      </section>

      <section className="card">
        <h2>Current Pantry</h2>

        {items.length === 0 ? (
          <p>No pantry items added yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Item</th>
                <th>Category</th>
                <th>Quantity</th>
                <th>Unit</th>
                <th>Barcode</th>
                <th>Brand</th>
                <th>Expiration</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.item_name}</td>
                  <td>{item.category}</td>
                  <td>{item.quantity}</td>
                  <td>{item.unit}</td>
                  <td>{item.barcode || "Manual"}</td>
                  <td>{item.brand || "N/A"}</td>
                  <td>{item.expiration_date || "N/A"}</td>
                  <td>
                    <button className="danger" onClick={() => remove(item.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
