import { useEffect, useState } from "react";
import { createWorker } from "tesseract.js";
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
    return "Could not connect to Smart Pantry. Please refresh the page and try again.";
  }

  return err.message || "Something went wrong.";
}

function guessCategory(itemName) {
  const name = String(itemName || "").toLowerCase();

  if (/(chicken|beef|turkey|fish|salmon|tuna|shrimp|egg|eggs|tofu|lamb|steak|meat)/.test(name)) {
    return "Protein";
  }

  if (/(milk|cheese|yogurt|cream|butter|dairy)/.test(name)) {
    return "Dairy";
  }

  if (/(rice|pasta|bread|tortilla|oat|oats|cereal|flour|noodle|noodles|bagel|bun|roll)/.test(name)) {
    return "Grain";
  }

  if (/(apple|banana|orange|berry|berries|grape|grapes|fruit|lemon|lime|peach|pear|melon)/.test(name)) {
    return "Fruit";
  }

  if (/(lettuce|spinach|broccoli|carrot|pepper|tomato|cucumber|vegetable|celery|potato|potatoes|corn|greens)/.test(name)) {
    return "Vegetable";
  }

  if (/(beans|soup|canned|tomato sauce|sauce|peas)/.test(name)) {
    return "Canned Goods";
  }

  if (/(frozen|ice cream|freezer)/.test(name)) {
    return "Frozen";
  }

  if (/(chips|crackers|cookie|cookies|snack|granola|popcorn|pretzel)/.test(name)) {
    return "Snack";
  }

  if (/(ketchup|mustard|mayo|mayonnaise|dressing|salsa|hot sauce|soy sauce|seasoning|spice|salt|pepper)/.test(name)) {
    return "Condiment";
  }

  if (/(juice|water|tea|coffee|soda|drink|beverage)/.test(name)) {
    return "Beverage";
  }

  return "Other";
}


function cleanReceiptLine(line) {
  return String(line || "")
    .replace(/[|]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function preprocessReceiptImage(file) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const reader = new FileReader();

    reader.onload = () => {
      image.onload = () => {
        const maxWidth = 1800;
        const scale =
          image.width < maxWidth
            ? Math.min(2, maxWidth / image.width)
            : maxWidth / image.width;

        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d", { willReadFrequently: true });

        canvas.width = Math.round(image.width * scale);
        canvas.height = Math.round(image.height * scale);

        ctx.fillStyle = "white";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.filter = "grayscale(100%) contrast(160%) brightness(118%)";
        ctx.drawImage(image, 0, 0, canvas.width, canvas.height);

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;

        for (let i = 0; i < data.length; i += 4) {
          const gray = data[i];
          const cleaned = gray > 175 ? 255 : gray < 105 ? 0 : gray;

          data[i] = cleaned;
          data[i + 1] = cleaned;
          data[i + 2] = cleaned;
        }

        ctx.putImageData(imageData, 0, 0);
        resolve(canvas.toDataURL("image/png"));
      };

      image.onerror = () => reject(new Error("Could not load receipt image."));
      image.src = reader.result;
    };

    reader.onerror = () => reject(new Error("Could not read receipt image."));
    reader.readAsDataURL(file);
  });
}

const FOOD_RECEIPT_SECTIONS = [
  "grocery",
  "produce",
  "meat",
  "seafood",
  "refrig",
  "frozen",
  "dairy",
  "deli",
  "bakery",
];

const NON_FOOD_RECEIPT_SECTIONS = [
  "groc nonedible",
  "nonedible",
  "miscellaneous",
  "pharmacy",
  "general mdse",
  "household",
];

const FOOD_WORDS = [
  "sandwich",
  "soy",
  "sauce",
  "sugar",
  "corn",
  "lamb",
  "beef",
  "chicken",
  "turkey",
  "fish",
  "salmon",
  "tuna",
  "shrimp",
  "egg",
  "eggs",
  "milk",
  "cheese",
  "yogurt",
  "butter",
  "rice",
  "pasta",
  "bread",
  "tortilla",
  "oats",
  "cereal",
  "lettuce",
  "spinach",
  "broccoli",
  "carrot",
  "tomato",
  "potato",
  "pepper",
  "grapefruit",
  "grpft",
  "apple",
  "banana",
  "orange",
  "berry",
  "juice",
  "coffee",
  "tea",
  "beans",
  "soup",
];

const NON_FOOD_WORDS = [
  "bag charge",
  "dspsbl",
  "disposable",
  "match",
  "light",
  "brquts",
  "briquets",
  "charcoal",
  "tax",
  "balance",
  "cashier",
  "sale savings",
  "savings",
];

function removeMoneyColumns(line) {
  return String(line || "")
    .replace(/\$\s?\d+(\.\d{2})?/g, " ")
    .replace(/\s+\d+\.\d{2}\s+\d+\.\d{2}\s?[A-Z]?$/i, " ")
    .replace(/\s+\d+\.\d{2}\s?[A-Z]?$/i, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function isReceiptHeaderOrFooter(line) {
  const value = String(line || "").toLowerCase().trim();

  if (!value) return true;
  if (value.length < 2) return true;

  const noisePatterns = [
    /\bjewel\b/i,
    /\bosco\b/i,
    /\bstore\b/i,
    /\bmain\b/i,
    /\bfreddie\b/i,
    /\bboyd\b/i,
    /\bstony\b/i,
    /\bisland\b/i,
    /\bchicago\b/i,
    /\bil\b/i,
    /\bphone\b/i,
    /\btel\b/i,
    /\brx\b/i,
    /\bcashier\b/i,
    /\bself\b/i,
    /\bprice\b/i,
    /\byou pay\b/i,
    /\bsubtotal\b/i,
    /\btotal\b/i,
    /\btax\b/i,
    /\bbalance\b/i,
    /\bcash\b/i,
    /\bcredit\b/i,
    /\bdebit\b/i,
    /\bvisa\b/i,
    /\bcard\b/i,
    /\bthank\b/i,
    /\breceipt\b/i,
    /\bbarcode\b/i,
    /\btransaction\b/i,
    /\bauth\b/i,
    /\bapproval\b/i,
    /\d{3}[-.\s]\d{3}[-.\s]\d{4}/,
    /\b\d{5}(-\d{4})?\b/,
  ];

  return noisePatterns.some((pattern) => pattern.test(value));
}

function getReceiptSection(line) {
  const value = String(line || "").toLowerCase().trim();

  if (!value) return "";

  if (value.includes("groc nonedible")) return "groc nonedible";
  if (value.includes("miscellaneous")) return "miscellaneous";
  if (value.includes("refrig") || value.includes("frozen")) return "refrig/frozen";
  if (value.includes("grocery")) return "grocery";
  if (value.includes("produce")) return "produce";
  if (value.includes("meat")) return "meat";
  if (value.includes("seafood")) return "seafood";
  if (value.includes("dairy")) return "dairy";
  if (value.includes("deli")) return "deli";
  if (value.includes("bakery")) return "bakery";

  return "";
}

function isFoodSection(section) {
  const value = String(section || "").toLowerCase();
  return FOOD_RECEIPT_SECTIONS.some((sectionName) => value.includes(sectionName));
}

function isNonFoodSection(section) {
  const value = String(section || "").toLowerCase();
  return NON_FOOD_RECEIPT_SECTIONS.some((sectionName) =>
    value.includes(sectionName)
  );
}

function extractWeight(line) {
  const value = String(line || "").toLowerCase();

  const lbMatch = value.match(/\b(\d+(\.\d+)?)\s?(lb|lbs|pound|pounds)\b/i);
  if (lbMatch) {
    return {
      quantity: Number(lbMatch[1]),
      unit: "lb",
    };
  }

  const ozMatch = value.match(/\b(\d+(\.\d+)?)\s?(oz|ounce|ounces|0z)\b/i);
  if (ozMatch) {
    return {
      quantity: Number(ozMatch[1]),
      unit: "oz",
    };
  }

  const ctMatch = value.match(/\b(\d+)\s?(ct|count|pk|pack)\b/i);
  if (ctMatch) {
    return {
      quantity: Number(ctMatch[1]),
      unit: "items",
    };
  }

  return {
    quantity: 1,
    unit: "item",
  };
}

function isWeightOnlyLine(line) {
  return /^\s*(wt\s+)?\d+(\.\d+)?\s?(lb|lbs|oz|ounce|ounces)\b/i.test(
    String(line || "").toLowerCase()
  );
}

function cleanFoodItemName(rawName) {
  return String(rawName || "")
    .replace(/\$\s?\d+(\.\d{2})?/g, " ")
    .replace(/\b\d+\.\d{2}\b/g, " ")
    .replace(/\b\d{4,14}\b/g, " ")
    .replace(/^\s*\d+\s?@\s*/i, " ")
    .replace(/\b\d+(\.\d+)?\s?(lb|lbs|pound|pounds|oz|ounce|ounces|0z|ct|count|pk|pack)\b/gi, " ")
    .replace(/\b(sale|savings|save|club|reward|rewards|member|price|you pay)\b/gi, " ")
    .replace(/\b(B|T|F)\b$/g, " ")
    .replace(/[^a-zA-Z0-9\s\-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function looksLikeFoodItem(name, section = "") {
  const value = String(name || "").toLowerCase().trim();

  if (!value) return false;
  if (value.length < 2) return false;
  if (isReceiptHeaderOrFooter(value)) return false;

  if (NON_FOOD_WORDS.some((word) => value.includes(word))) {
    return false;
  }

  if (FOOD_WORDS.some((word) => value.includes(word))) {
    return true;
  }

  if (isFoodSection(section) && !isNonFoodSection(section)) {
    return true;
  }

  return false;
}

function parseProductLine(line, section) {
  const value = removeMoneyColumns(cleanReceiptLine(line));
  const match = value.match(/^\s*(\d{4,14})\s+(.+)$/);

  if (!match) return null;

  const barcode = match[1];
  const rawName = match[2];

  if (isNonFoodSection(section)) return null;

  const weight = extractWeight(rawName);
  const itemName = cleanFoodItemName(rawName);

  if (!looksLikeFoodItem(itemName, section)) return null;

  return {
    selected: true,
    item_name: itemName,
    category: guessCategory(itemName),
    quantity: weight.quantity,
    unit: weight.unit,
    container_type: "",
    expiration_date: "",
    barcode,
    brand: "",
    source: "receipt_ocr",
    notes: "Added from receipt OCR / grocery input",
  };
}

function parseGroceryText(text) {
  const lines = String(text || "")
    .split(/\n|,/)
    .map(cleanReceiptLine)
    .filter(Boolean);

  const items = [];
  const seen = new Set();
  let currentSection = "";

  for (const line of lines) {
    const section = getReceiptSection(line);

    if (section) {
      currentSection = section;
      continue;
    }

    if (isReceiptHeaderOrFooter(line)) {
      continue;
    }

    if (/sale savings|savings|you pay|price/i.test(line)) {
      continue;
    }

    if (isWeightOnlyLine(line) && items.length > 0) {
      const weight = extractWeight(line);
      const lastIndex = items.length - 1;

      if (items[lastIndex].unit === "item") {
        items[lastIndex] = {
          ...items[lastIndex],
          quantity: weight.quantity,
          unit: weight.unit,
        };
      }

      continue;
    }

    const item = parseProductLine(line, currentSection);

    if (!item) continue;

    const key = `${item.barcode}-${item.item_name}`.toLowerCase();

    if (seen.has(key)) continue;

    seen.add(key);
    items.push(item);
  }

  return items.slice(0, 30);
}



export default function Pantry() {
  const user = getUser();

  const [items, setItems] = useState([]);
  const [editedItems, setEditedItems] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [barcodeSearch, setBarcodeSearch] = useState("");

  const [receiptFile, setReceiptFile] = useState(null);
  const [receiptPreview, setReceiptPreview] = useState("");
  const [ocrText, setOcrText] = useState("");
  const [ocrProgress, setOcrProgress] = useState(0);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [detectedItems, setDetectedItems] = useState([]);

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

  function changeDetected(index, field, value) {
    setDetectedItems((prev) =>
      prev.map((item, itemIndex) =>
        itemIndex === index
          ? {
              ...item,
              [field]: value,
            }
          : item
      )
    );
  }

  function handleReceiptFile(e) {
    const file = e.target.files?.[0];

    setMessage("");
    setError("");
    setOcrText("");
    setDetectedItems([]);
    setOcrProgress(0);

    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Please choose a receipt image from your phone or computer.");
      return;
    }

    const previewUrl = URL.createObjectURL(file);
    setReceiptFile(file);
    setReceiptPreview(previewUrl);
    setMessage("Receipt image loaded. Click Scan Receipt with OCR next.");
  }

  
function clearReceiptScan() {
  if (receiptPreview) {
    URL.revokeObjectURL(receiptPreview);
  }

  setReceiptFile(null);
  setReceiptPreview("");
  setOcrText("");
  setDetectedItems([]);
  setOcrProgress(0);
  setMessage("");
  setError("");

  const fileInput = document.querySelector('input[type="file"][accept*="image"]');
  if (fileInput) {
    fileInput.value = "";
  }
}

async function scanReceiptWithOcr() {
    setMessage("");
    setError("");

    if (!receiptFile && !receiptPreview) {
      setError("Take or upload a receipt photo first.");
      return;
    }

    setOcrLoading(true);
    setOcrProgress(0);

    let worker = null;

    try {
      worker = await createWorker("eng", 1, {
        logger: (m) => {
          if (m.status === "recognizing text" && typeof m.progress === "number") {
            setOcrProgress(Math.round(m.progress * 100));
          }
        },
      });

      const imageForOcr = receiptFile
        ? await preprocessReceiptImage(receiptFile)
        : receiptPreview;

      const {
        data: { text },
      } = await worker.recognize(imageForOcr);

      console.log("Smart Pantry OCR text:", text);

      setOcrText(text || "");

      const detected = parseGroceryText(text || "");
      setDetectedItems(detected);

      if (detected.length === 0) {
        setMessage("OCR finished, but no clear grocery items were detected. You can edit the text and detect again.");
      } else {
        setMessage(`OCR finished. ${detected.length} possible item(s) detected. Review before saving.`);
      }
    } catch (err) {
      setError(`OCR failed: ${err.message || "Could not scan this receipt image."}`);
    } finally {
      if (worker) {
        await worker.terminate();
      }

      setOcrLoading(false);
    }
  }

  function detectItemsFromText() {
    setMessage("");
    setError("");

    const detected = parseGroceryText(ocrText);

    if (detected.length === 0) {
      setError("No grocery items were detected. Try editing the text so each item is on its own line.");
      return;
    }

    setDetectedItems(detected);
    setMessage(`${detected.length} possible item(s) detected. Review before saving.`);
  }


  function useOcrLinesAsItems() {
    setMessage("");
    setError("");

    const fallbackItems = parseGroceryText(ocrText).map((item) => ({
      ...item,
      source: "receipt_ocr_fallback",
      notes: "Added from OCR line review",
    }));

    if (fallbackItems.length === 0) {
      setError("No receipt item rows were found. Try a clearer photo or type item rows manually with the UPC first.");
      return;
    }

    setDetectedItems(fallbackItems);
    setMessage(`${fallbackItems.length} receipt item row(s) moved into review. Edit before saving.`);
  }

  async function handleGroceryTextFile(e) {
    const file = e.target.files?.[0];

    setMessage("");
    setError("");

    if (!file) return;

    try {
      const text = await file.text();
      setOcrText(text);
      setDetectedItems(parseGroceryText(text));
      setMessage("Text file loaded. Review the detected items before saving.");
    } catch {
      setError("Could not read that file. Try a .txt or .csv file.");
    }
  }

  async function addDetectedItems() {
    setMessage("");
    setError("");

    const selected = detectedItems.filter((item) => item.selected);

    if (selected.length === 0) {
      setError("Select at least one detected item to add.");
      return;
    }

    try {
      for (const item of selected) {
        await api.addPantryItem({
          ...item,
          user_id: user.id,
          quantity: Number(item.quantity || 0),
        });
      }

      setDetectedItems([]);
      setOcrText("");
      setReceiptFile(null);
      setReceiptPreview("");
      setOcrProgress(0);
      setMessage(`${selected.length} item(s) added to pantry.`);
      await load();
    } catch (err) {
      setError(friendlyFetchError(err));
    }
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

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const expiringSoonCount = editedItems.filter((item) => {
    if (!item.expiration_date) return false;
    const date = new Date(`${item.expiration_date}T00:00:00`);
    const days = Math.ceil((date - today) / 86400000);
    return days >= 0 && days <= 4;
  }).length;

  const categoryCount = new Set(
    editedItems.map((item) => item.category).filter(Boolean)
  ).size;

  return (
    <div className="pantryPage m8PantryPage">
      <section className="m8PantryHero">
        <div>
          <p className="eyebrow">Pantry inventory</p>
          <h1>My Pantry</h1>
          <p>
            Keep this list current so Smart Pantry can give you stronger meal
            recommendations and help you notice foods that should be used soon.
          </p>
        </div>

        <div className="m8PantryHeroStats" aria-label="Pantry summary">
          <div>
            <strong>{editedItems.length}</strong>
            <span>Total items</span>
          </div>
          <div>
            <strong>{expiringSoonCount}</strong>
            <span>Use soon</span>
          </div>
          <div>
            <strong>{categoryCount}</strong>
            <span>Categories</span>
          </div>
        </div>
      </section>

      <section className="m8PantryMethodGrid" aria-label="Ways to add pantry items">
        <article className="card m8PantryMethodCard isActive">
          <span className="m8MethodNumber">1</span>
          <div>
            <h2>Add an item</h2>
            <p>Enter one pantry item and its expiration information.</p>
          </div>
        </article>
        <article className="card m8PantryMethodCard">
          <span className="m8MethodNumber">2</span>
          <div>
            <h2>Search a UPC</h2>
            <p>Use the product barcode to fill in available details.</p>
          </div>
        </article>
        <article className="card m8PantryMethodCard">
          <span className="m8MethodNumber">3</span>
          <div>
            <h2>Scan a receipt</h2>
            <p>Review OCR results before adding selected groceries.</p>
          </div>
        </article>
      </section>

      <section className="card m8PantryEntryCard">
        <div className="m8SectionHeading">
          <div>
            <p className="eyebrow">Add to your pantry</p>
            <h2>Item details</h2>
            <p>
              Item name and quantity are required. Adding a category and
              expiration date makes your dashboard and recommendations more useful.
            </p>
          </div>
        </div>

        <div className="m8PantryEntryLayout">
          <form className="m8PantryForm" onSubmit={addItem}>
            <div className="m8PantryField m8FieldWide">
              <label htmlFor="pantry-item-name">Item name</label>
              <input
                id="pantry-item-name"
                placeholder="Example: chicken breast"
                value={form.item_name}
                onChange={(e) => change("item_name", e.target.value)}
                required
              />
            </div>

            <div className="m8PantryField">
              <label htmlFor="pantry-category">Category</label>
              <select
                id="pantry-category"
                value={form.category}
                onChange={(e) => change("category", e.target.value)}
              >
                {CATEGORY_OPTIONS.map((category) => (
                  <option key={category}>{category}</option>
                ))}
              </select>
            </div>

            <div className="m8PantryField">
              <label htmlFor="pantry-quantity">Quantity</label>
              <input
                id="pantry-quantity"
                type="number"
                step="0.1"
                min="0"
                value={form.quantity}
                onChange={(e) => change("quantity", e.target.value)}
                required
              />
            </div>

            <div className="m8PantryField">
              <label htmlFor="pantry-unit">Unit</label>
              <select
                id="pantry-unit"
                value={form.unit}
                onChange={(e) => change("unit", e.target.value)}
              >
                {UNIT_OPTIONS.map((unit) => (
                  <option key={unit}>{unit}</option>
                ))}
              </select>
            </div>

            <div className="m8PantryField">
              <label htmlFor="pantry-container">Container type</label>
              <select
                id="pantry-container"
                value={form.container_type}
                onChange={(e) => change("container_type", e.target.value)}
              >
                <option value="">Select a container</option>
                {CONTAINER_OPTIONS.filter(Boolean).map((container) => (
                  <option key={container}>{container}</option>
                ))}
              </select>
            </div>

            <div className="m8PantryField">
              <label htmlFor="pantry-expiration">Expiration date</label>
              <input
                id="pantry-expiration"
                type="date"
                value={form.expiration_date}
                onChange={(e) => change("expiration_date", e.target.value)}
              />
              <small>Use the package date or your best estimate.</small>
            </div>

            <div className="m8PantryField">
              <label htmlFor="pantry-brand">Brand <span>(optional)</span></label>
              <input
                id="pantry-brand"
                placeholder="Example: Tyson"
                value={form.brand}
                onChange={(e) => change("brand", e.target.value)}
              />
            </div>

            <div className="m8PantryField">
              <label htmlFor="pantry-barcode">Barcode / UPC <span>(optional)</span></label>
              <input
                id="pantry-barcode"
                placeholder="Enter the number below the barcode"
                value={form.barcode}
                onChange={(e) => change("barcode", e.target.value)}
              />
            </div>

            <div className="m8PantryField m8FieldWide">
              <label htmlFor="pantry-notes">Notes <span>(optional)</span></label>
              <input
                id="pantry-notes"
                placeholder="Example: opened, frozen, or half-full"
                value={form.notes}
                onChange={(e) => change("notes", e.target.value)}
              />
            </div>

            <button className="m8PrimaryAction m8FieldWide" type="submit">
              Add item to pantry
            </button>
          </form>

          <aside className="m8UpcPanel">
            <p className="eyebrow">Faster entry</p>
            <h3>Look up a product</h3>
            <p>
              Enter the UPC printed below a product barcode. When a match is
              available, Smart Pantry will fill in the product name and brand for review.
            </p>

            <form className="m8UpcForm" onSubmit={lookupBarcode}>
              <label htmlFor="pantry-upc-search">Barcode or UPC</label>
              <input
                id="pantry-upc-search"
                value={barcodeSearch}
                onChange={(e) => setBarcodeSearch(e.target.value)}
                placeholder="Example: 012345678905"
              />
              <button type="submit" disabled={barcodeLoading}>
                {barcodeLoading ? "Searching…" : "Search product"}
              </button>
            </form>

            <div className="m8UpcTip">
              <strong>Before adding:</strong>
              <span>Review the product name, quantity, unit, and expiration date.</span>
            </div>
          </aside>
        </div>

        {message && <p className="success m8PantryNotice" role="status">{message}</p>}
        {error && <p className="error m8PantryNotice" role="alert">{error}</p>}
      </section>

      <section className="card pantryFormCard receiptOcrCard m8ReceiptCard">
        <div className="m8SectionHeading m8ReceiptHeading">
          <div>
            <p className="eyebrow">Receipt-assisted entry</p>
            <h2>Scan or upload a grocery receipt</h2>
            <p>
              OCR can suggest grocery items from a receipt image or text list.
              Because receipt text is not always exact, review every item before saving it.
            </p>
          </div>
          {(receiptFile || receiptPreview || ocrText || detectedItems.length > 0) && (
            <button
              type="button"
              className="secondaryButton"
              onClick={clearReceiptScan}
            >
              Clear receipt
            </button>
          )}
        </div>

        <div className="m8ReceiptSteps">
          <div><strong>1</strong><span>Upload a clear image or text list</span></div>
          <div><strong>2</strong><span>Scan or detect possible items</span></div>
          <div><strong>3</strong><span>Edit, select, and save</span></div>
        </div>

        <div className="receiptUploadBox m8ReceiptUploadBox">
          <label className="receiptUploadButton">
            Take photo or upload image
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleReceiptFile}
            />
          </label>

          <label className="receiptUploadButton secondaryUpload">
            Upload TXT or CSV list
            <input
              type="file"
              accept=".txt,.csv"
              onChange={handleGroceryTextFile}
            />
          </label>

          <button
            type="button"
            className="scanReceiptButton"
            onClick={scanReceiptWithOcr}
            disabled={ocrLoading}
          >
            {ocrLoading ? `Scanning… ${ocrProgress}%` : "Scan receipt with OCR"}
          </button>
        </div>

        {receiptPreview && (
          <div className="receiptPreviewGrid">
            <div>
              <strong>Receipt preview</strong>
              <img src={receiptPreview} alt="Uploaded receipt preview" />
            </div>

            <div>
              <strong>Scan progress</strong>
              <div className="ocrProgressBar" aria-label={`OCR progress ${ocrProgress}%`}>
                <span style={{ width: `${ocrProgress}%` }} />
              </div>
              <p>
                For better results, place the receipt flat, avoid shadows, and
                make sure the item names are readable.
              </p>
            </div>
          </div>
        )}

        <label className="m8OcrTextLabel" htmlFor="ocr-receipt-text">
          Receipt text or grocery list
        </label>
        <textarea
          id="ocr-receipt-text"
          className="ocrTextArea"
          value={ocrText}
          onChange={(e) => setOcrText(e.target.value)}
          placeholder={"Scanned text will appear here. You may also type or paste one grocery item per line:\neggs\nmilk\nchicken breast\nrice\nlettuce"}
        />

        <div className="groceryInputActions m8GroceryInputActions">
          <button type="button" onClick={detectItemsFromText}>
            Detect items from text
          </button>

          <button type="button" className="secondaryButton" onClick={useOcrLinesAsItems}>
            Move lines to review
          </button>
        </div>

        {detectedItems.length > 0 && (
          <div className="detectedReviewBox m8DetectedReviewBox">
            <div className="m8ReviewHeading">
              <div>
                <h3>Review detected items</h3>
                <p>
                  Select only the groceries you want to add. Correct the item
                  details and expiration dates before saving.
                </p>
              </div>
              <span>{detectedItems.filter((item) => item.selected).length} selected</span>
            </div>

            <div className="detectedTableWrap">
              <table className="detectedTable">
                <thead>
                  <tr>
                    <th>Add</th>
                    <th>Item</th>
                    <th>UPC / PLU</th>
                    <th>Category</th>
                    <th>Qty</th>
                    <th>Unit</th>
                    <th>Container</th>
                    <th>Expiration</th>
                  </tr>
                </thead>

                <tbody>
                  {detectedItems.map((item, index) => (
                    <tr key={`${item.item_name}-${index}`}>
                      <td>
                        <input
                          type="checkbox"
                          aria-label={`Add ${item.item_name || `item ${index + 1}`}`}
                          checked={item.selected}
                          onChange={(e) =>
                            changeDetected(index, "selected", e.target.checked)
                          }
                        />
                      </td>
                      <td>
                        <input
                          value={item.item_name}
                          onChange={(e) =>
                            changeDetected(index, "item_name", e.target.value)
                          }
                        />
                      </td>
                      <td>
                        <input
                          value={item.barcode}
                          onChange={(e) =>
                            changeDetected(index, "barcode", e.target.value)
                          }
                          placeholder="UPC / PLU"
                        />
                      </td>
                      <td>
                        <select
                          value={item.category}
                          onChange={(e) =>
                            changeDetected(index, "category", e.target.value)
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
                            changeDetected(index, "quantity", e.target.value)
                          }
                        />
                      </td>
                      <td>
                        <select
                          value={item.unit}
                          onChange={(e) =>
                            changeDetected(index, "unit", e.target.value)
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
                            changeDetected(index, "container_type", e.target.value)
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
                            changeDetected(index, "expiration_date", e.target.value)
                          }
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button className="addDetectedButton" onClick={addDetectedItems}>
              Add selected items to pantry
            </button>
          </div>
        )}
      </section>

      <section className="card pantryTableCard m8PantryTableCard">
        <div className="pantrySectionHeader m8PantryTableHeader">
          <div>
            <p className="eyebrow">Your saved inventory</p>
            <h2>Current pantry</h2>
            <p>
              Update a row, then select Save. Reset restores the last saved
              version, while Delete permanently removes that item.
            </p>
          </div>

          <span>{editedItems.length} item{editedItems.length === 1 ? "" : "s"}</span>
        </div>

        {loading ? (
          <div className="m8PantryEmptyState">Loading pantry items…</div>
        ) : editedItems.length === 0 ? (
          <div className="m8PantryEmptyState">
            <strong>Your pantry is empty.</strong>
            <span>Add your first item above to begin receiving meal recommendations.</span>
          </div>
        ) : (
          <div className="realTableWrap m8PantryTableWrap">
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
                        aria-label={`Item name for row ${rowIndex + 1}`}
                        value={item.item_name}
                        onChange={(e) =>
                          changeTable(rowIndex, "item_name", e.target.value)
                        }
                      />
                    </td>
                    <td>
                      <select
                        aria-label={`Category for ${item.item_name}`}
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
                        aria-label={`Quantity for ${item.item_name}`}
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
                        aria-label={`Unit for ${item.item_name}`}
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
                        aria-label={`Container for ${item.item_name}`}
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
                        aria-label={`Expiration date for ${item.item_name}`}
                        type="date"
                        value={item.expiration_date}
                        onChange={(e) =>
                          changeTable(rowIndex, "expiration_date", e.target.value)
                        }
                      />
                    </td>
                    <td>
                      <input
                        aria-label={`Brand for ${item.item_name}`}
                        value={item.brand}
                        onChange={(e) =>
                          changeTable(rowIndex, "brand", e.target.value)
                        }
                      />
                    </td>
                    <td>
                      <input
                        aria-label={`UPC for ${item.item_name}`}
                        value={item.barcode}
                        onChange={(e) =>
                          changeTable(rowIndex, "barcode", e.target.value)
                        }
                      />
                    </td>
                    <td>
                      <input
                        aria-label={`Notes for ${item.item_name}`}
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
