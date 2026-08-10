import { useEffect, useRef, useState } from "react";
import { createWorker } from "tesseract.js";
import { BrowserMultiFormatReader } from "@zxing/browser";
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
  "gallon",
  "gallons",
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


function parseCsvRows(text) {
  const rows = [];
  let row = [];
  let value = "";
  let inQuotes = false;
  const source = String(text || "").replace(/^\uFEFF/, "");

  for (let i = 0; i < source.length; i += 1) {
    const char = source[i];
    const next = source[i + 1];

    if (char === '"') {
      if (inQuotes && next === '"') {
        value += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === ',' && !inQuotes) {
      row.push(value);
      value = "";
      continue;
    }

    if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && next === '\n') i += 1;
      row.push(value);
      if (row.some((cell) => String(cell).trim() !== "")) rows.push(row);
      row = [];
      value = "";
      continue;
    }

    value += char;
  }

  row.push(value);
  if (row.some((cell) => String(cell).trim() !== "")) rows.push(row);
  return rows;
}

function parsePantryNoteTrackerCsv(text) {
  const rows = parseCsvRows(text);
  if (rows.length < 2) return null;

  const headers = rows[0].map((cell) => String(cell || "").trim().toLowerCase());
  const required = ["item_name", "quantity", "unit", "category", "expiration_date", "notes"];
  const isTrackerCsv = required.every((header) => headers.includes(header));
  if (!isTrackerCsv) return null;

  const indexFor = (name) => headers.indexOf(name);
  const items = [];

  for (const row of rows.slice(1)) {
    const itemName = String(row[indexFor("item_name")] || "").trim();
    if (!itemName) continue;

    const rawQuantity = String(row[indexFor("quantity")] || "").trim();
    const parsedQuantity = Number(rawQuantity);
    const rawUnit = String(row[indexFor("unit")] || "").trim();
    const rawCategory = String(row[indexFor("category")] || "").trim();
    const rawExpiration = String(row[indexFor("expiration_date")] || "").trim();
    const rawNotes = String(row[indexFor("notes")] || "").trim();

    const unit = UNIT_OPTIONS.includes(rawUnit) ? rawUnit : "item";
    const category = CATEGORY_OPTIONS.includes(rawCategory)
      ? rawCategory
      : guessCategory(itemName);

    items.push({
      selected: true,
      item_name: itemName,
      category,
      quantity: Number.isFinite(parsedQuantity) && parsedQuantity > 0 ? parsedQuantity : 1,
      unit,
      container_type: "",
      expiration_date: cleanDate(rawExpiration),
      barcode: "",
      brand: "",
      source: "pantry_note_tracker_csv",
      notes: rawNotes,
    });
  }

  return items;
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




function categoryIcon(category) {
  const icons = {
    Protein: "🍗",
    Dairy: "🥛",
    Grain: "🍚",
    Fruit: "🍎",
    Vegetable: "🥬",
    "Canned Goods": "🥫",
    Frozen: "❄️",
    Snack: "🍿",
    Condiment: "🫙",
    Beverage: "🧃",
    Other: "🛒",
  };

  return icons[category] || icons.Other;
}

export default function Pantry() {
  const user = getUser();

  const [items, setItems] = useState([]);
  const [editedItems, setEditedItems] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [barcodeSearch, setBarcodeSearch] = useState("");
  const [entryMode, setEntryMode] = useState("product");
  const [productTool, setProductTool] = useState("");
  const [pantrySearch, setPantrySearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [useSoonOnly, setUseSoonOnly] = useState(false);

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
  const [scannerOpen, setScannerOpen] = useState(false);
  const [scannerMessage, setScannerMessage] = useState("");
  const [scannerStarting, setScannerStarting] = useState(false);
  const scannerVideoRef = useRef(null);
  const scannerControlsRef = useRef(null);
  const scannerReaderRef = useRef(null);

  const [receiptCameraOpen, setReceiptCameraOpen] = useState(false);
  const [receiptCameraStarting, setReceiptCameraStarting] = useState(false);
  const [receiptCameraMessage, setReceiptCameraMessage] = useState("");
  const receiptVideoRef = useRef(null);
  const receiptStreamRef = useRef(null);

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

    return () => {
      if (scannerControlsRef.current) {
        scannerControlsRef.current.stop();
      }

      if (scannerVideoRef.current?.srcObject) {
        scannerVideoRef.current.srcObject.getTracks().forEach((track) => track.stop());
      }

      if (receiptStreamRef.current) {
        receiptStreamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
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

  function loadReceiptImage(file, successMessage = "Receipt image loaded. Click Scan Receipt with OCR next.") {
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

    if (receiptPreview) {
      URL.revokeObjectURL(receiptPreview);
    }

    const previewUrl = URL.createObjectURL(file);
    setReceiptFile(file);
    setReceiptPreview(previewUrl);
    setMessage(successMessage);
  }

  function handleReceiptFile(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    loadReceiptImage(file);
  }

  function stopReceiptCamera() {
    if (receiptStreamRef.current) {
      receiptStreamRef.current.getTracks().forEach((track) => track.stop());
      receiptStreamRef.current = null;
    }

    if (receiptVideoRef.current) {
      receiptVideoRef.current.srcObject = null;
    }

    setReceiptCameraStarting(false);
  }

  function closeReceiptCamera() {
    stopReceiptCamera();
    setReceiptCameraOpen(false);
    setReceiptCameraMessage("");
  }

  async function startReceiptCamera() {
    setMessage("");
    setError("");
    setReceiptCameraMessage("Position the full receipt inside the frame.");
    setReceiptCameraOpen(true);
    setReceiptCameraStarting(true);

    await new Promise((resolve) => setTimeout(resolve, 0));

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Camera access is not supported by this browser.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      });

      receiptStreamRef.current = stream;

      if (!receiptVideoRef.current) {
        throw new Error("The camera preview could not be created.");
      }

      receiptVideoRef.current.srcObject = stream;
      await receiptVideoRef.current.play();
      setReceiptCameraStarting(false);
      setReceiptCameraMessage("Keep the receipt flat, avoid glare, then capture the photo.");
    } catch (err) {
      stopReceiptCamera();
      setReceiptCameraOpen(false);
      setReceiptCameraMessage("");
      setError(
        err?.name === "NotAllowedError"
          ? "Camera permission was blocked. Allow camera access in your browser, then try again."
          : err?.message || "The receipt camera could not start. Use Upload Image instead."
      );
    }
  }

  async function captureReceiptPhoto() {
    const video = receiptVideoRef.current;

    if (!video || !video.videoWidth || !video.videoHeight) {
      setReceiptCameraMessage("The camera is still starting. Wait a moment and try again.");
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.94));

    if (!blob) {
      setReceiptCameraMessage("The photo could not be captured. Please try again.");
      return;
    }

    const file = new File([blob], `receipt-${Date.now()}.jpg`, { type: "image/jpeg" });
    closeReceiptCamera();
    loadReceiptImage(file, "Receipt photo captured. Review it, then click Scan with OCR.");
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
    e.target.value = "";

    setMessage("");
    setError("");

    if (!file) return;

    try {
      const text = await file.text();
      const trackerItems = file.name.toLowerCase().endsWith(".csv")
        ? parsePantryNoteTrackerCsv(text)
        : null;

      if (trackerItems) {
        if (trackerItems.length === 0) {
          setDetectedItems([]);
          setOcrText("");
          setError("This Pantry Note Tracker CSV does not contain any pantry items to import.");
          return;
        }

        const existingKeys = new Set(
          items.map((item) => `${String(item.item_name || "").trim().toLowerCase()}|${cleanDate(item.expiration_date)}`)
        );
        let duplicateCount = 0;
        const reviewedItems = trackerItems.map((item) => {
          const key = `${item.item_name.trim().toLowerCase()}|${cleanDate(item.expiration_date)}`;
          if (existingKeys.has(key)) {
            duplicateCount += 1;
            return { ...item, selected: false };
          }
          return item;
        });

        setOcrText("");
        setDetectedItems(reviewedItems);
        setMessage(
          `${reviewedItems.length} Pantry Note Tracker item(s) ready for review.${duplicateCount ? ` ${duplicateCount} possible duplicate(s) were left unselected.` : ""}`
        );
        return;
      }

      setOcrText(text);
      const detected = parseGroceryText(text);
      setDetectedItems(detected);
      setMessage(
        detected.length
          ? `Grocery file loaded. ${detected.length} possible item(s) detected. Review before saving.`
          : "File loaded, but no grocery items were detected. Try one item per line or use a Pantry Note Tracker CSV export."
      );
    } catch {
      setError("Could not read that file. Try a .txt or Pantry Note Tracker .csv file.");
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

  function stopBarcodeScanner() {
    if (scannerControlsRef.current) {
      scannerControlsRef.current.stop();
      scannerControlsRef.current = null;
    }

    if (scannerStreamRef.current) {
      scannerStreamRef.current.getTracks().forEach((track) => track.stop());
      scannerStreamRef.current = null;
    }

    if (scannerVideoRef.current?.srcObject) {
      scannerVideoRef.current.srcObject.getTracks().forEach((track) => track.stop());
      scannerVideoRef.current.srcObject = null;
    }

    scannerReaderRef.current = null;
    setScannerStarting(false);
  }

  function closeBarcodeScanner() {
    stopBarcodeScanner();
    setScannerOpen(false);
    setScannerMessage("");
  }

  async function startBarcodeScanner() {
    setProductTool("scan");
    setMessage("");
    setError("");
    setScannerMessage("Starting your camera…");
    setScannerOpen(true);
    setScannerStarting(true);

    // Let React mount the video element before attaching the stream.
    await new Promise((resolve) => setTimeout(resolve, 50));

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Camera access is not supported in this browser.");
      }

      // Use the same browser camera path as the working receipt camera.
      // This avoids relying on camera labels/device enumeration before permission.
      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: "environment" },
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
          audio: false,
        });
      } catch (primaryError) {
        // Desktop webcams sometimes reject facingMode constraints.
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
      }

      scannerStreamRef.current = stream;

      if (!scannerVideoRef.current) {
        throw new Error("The barcode camera preview could not be created.");
      }

      scannerVideoRef.current.srcObject = stream;
      await scannerVideoRef.current.play();

      const reader = new BrowserMultiFormatReader();
      scannerReaderRef.current = reader;

      const controls = await reader.decodeFromStream(
        stream,
        scannerVideoRef.current,
        (result, error, controlsFromCallback) => {
          if (!result) return;

          const scannedValue = result.getText().trim();
          if (!scannedValue) return;

          setBarcodeSearch(scannedValue);
          setForm((previous) => ({
            ...previous,
            barcode: scannedValue,
          }));
          setScannerMessage(`Barcode detected: ${scannedValue}`);

          try {
            controlsFromCallback?.stop?.();
          } catch {
            // The regular stop routine below is still authoritative.
          }

          stopBarcodeScanner();
          setScannerOpen(false);
          void lookupBarcodeValue(scannedValue);
        }
      );

      scannerControlsRef.current = controls;
      setScannerStarting(false);
      setScannerMessage("Point the camera at one barcode and hold it steady inside the box.");
    } catch (err) {
      stopBarcodeScanner();
      setScannerMessage("");
      const blocked = ["NotAllowedError", "PermissionDeniedError"].includes(err?.name);
      setError(
        blocked
          ? "Camera permission was blocked. Allow camera access for this site in your browser, then try Scan Camera again."
          : err?.message || "The barcode camera could not start. Use Upload Photo or Enter UPC instead."
      );
      setScannerOpen(false);
    }
  }

  async function scanBarcodePhoto(event) {
    setProductTool("photo");
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) return;

    setMessage("");
    setError("");
    setBarcodeLoading(true);

    const objectUrl = URL.createObjectURL(file);

    try {
      const reader = new BrowserMultiFormatReader();
      const result = await reader.decodeFromImageUrl(objectUrl);
      const scannedValue = result.getText().trim();

      setBarcodeSearch(scannedValue);
      setForm((previous) => ({
        ...previous,
        barcode: scannedValue,
      }));

      await lookupBarcodeValue(scannedValue);
    } catch {
      setError(
        "No readable barcode was found in that photo. Try a closer, brighter picture with the full barcode visible."
      );
    } finally {
      URL.revokeObjectURL(objectUrl);
      setBarcodeLoading(false);
    }
  }

  async function lookupBarcodeValue(rawBarcode) {
    setProductTool("manual");
    setMessage("");
    setError("");

    const barcode = String(rawBarcode || "").trim();
    if (!barcode) {
      setError("Enter, scan, or upload a barcode first.");
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
          // Try the next supported endpoint path.
        }
      }

      if (!data) {
        setForm((previous) => ({ ...previous, barcode }));
        setError(
          `Barcode ${barcode} was read, but no product match was found. You can still enter the item details manually.`
        );
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
      const rawCategory =
        product.category || product.food_category || product.main_category || "Other";
      const category = CATEGORY_OPTIONS.includes(rawCategory)
        ? rawCategory
        : guessCategory(itemName);

      setBarcodeSearch(barcode);
      setForm((previous) => ({
        ...previous,
        item_name: itemName || previous.item_name,
        brand: brand || previous.brand,
        barcode,
        category,
        quantity: product.quantity || previous.quantity,
        unit: UNIT_OPTIONS.includes(product.unit) ? product.unit : previous.unit,
        container_type: product.container_type || previous.container_type,
        source: product.source || "barcode_lookup",
        notes: previous.notes || "Found by barcode lookup",
      }));

      setMessage(
        itemName
          ? `Barcode found: ${itemName}. Review the details and add the expiration date.`
          : "Barcode found. Review the item details before adding."
      );
    } catch (err) {
      setError(friendlyFetchError(err));
    } finally {
      setBarcodeLoading(false);
    }
  }

  async function lookupBarcode(e) {
    e.preventDefault();
    await lookupBarcodeValue(barcodeSearch);
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


  function chooseEntryMode(mode) {
    setEntryMode(mode);
    setMessage("");
    setError("");
    if (mode === "product") {
      setDetectedItems([]);
    }
  }

  function daysUntilExpiration(value) {
    if (!value) return null;
    const date = new Date(`${value}T00:00:00`);
    return Math.ceil((date - today) / 86400000);
  }

  function pantryStatus(item) {
    const days = daysUntilExpiration(item.expiration_date);
    if (days === null) return { label: "No date", className: "neutral" };
    if (days <= 0) return { label: "Use now", className: "urgent" };
    if (days <= 4) return { label: `${days} day${days === 1 ? "" : "s"}`, className: "soon" };
    return { label: `${days} days`, className: "fresh" };
  }

  const categoryOptionsForFilter = Array.from(
    new Set(editedItems.map((item) => item.category).filter(Boolean))
  ).sort();

  const filteredPantryItems = editedItems.filter((item) => {
    const query = pantrySearch.trim().toLowerCase();
    const matchesSearch =
      !query ||
      String(item.item_name || "").toLowerCase().includes(query) ||
      String(item.brand || "").toLowerCase().includes(query);

    const matchesCategory =
      categoryFilter === "all" || item.category === categoryFilter;

    const days = daysUntilExpiration(item.expiration_date);
    const matchesUseSoon = !useSoonOnly || (days !== null && days >= 0 && days <= 4);

    return matchesSearch && matchesCategory && matchesUseSoon;
  });

  return (
    <div className="pantryPage compactPantryPage">
      <section className="compactPantryHero">
        <div className="compactPantryHeroCopy">
          <p className="eyebrow">Pantry inventory</p>
          <h1>My Pantry</h1>
          <p>
            Add items quickly by scanning a barcode, uploading a photo, or entering them manually.
          </p>
        </div>

        <div className="compactPantryIllustration" aria-hidden="true">
          <span>🥬</span>
          <span>🥛</span>
          <span>🍅</span>
          <span>🥕</span>
          <span>🍞</span>
        </div>

        <div className="compactPantryStats" aria-label="Pantry summary">
          <article>
            <span className="statIcon green">▣</span>
            <strong>{editedItems.length}</strong>
            <small>Items in pantry</small>
          </article>
          <article>
            <span className="statIcon orange">◷</span>
            <strong>{expiringSoonCount}</strong>
            <small>Use soon</small>
          </article>
          <article>
            <span className="statIcon blue">◆</span>
            <strong>{categoryCount}</strong>
            <small>Categories</small>
          </article>
        </div>
      </section>

      <div className="compactPantryUtilityRow">
        <section className="card compactQuickAddCard">
        <div className="compactQuickAddHeader">
          <div>
            <p className="eyebrow">Add items to your pantry</p>
            <h2>Quick add</h2>
          </div>
        </div>

        <div className="compactEntryTabs" role="tablist" aria-label="Pantry entry type">
          <button
            type="button"
            role="tab"
            aria-selected={entryMode === "product"}
            className={entryMode === "product" ? "active" : ""}
            onClick={() => chooseEntryMode("product")}
          >
            <span aria-hidden="true">▥</span>
            Product Barcode
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={entryMode === "receipt"}
            className={entryMode === "receipt" ? "active" : ""}
            onClick={() => chooseEntryMode("receipt")}
          >
            <span aria-hidden="true">▤</span>
            Grocery Receipt
          </button>
        </div>

        {entryMode === "product" ? (
          <>
            <div className="compactActionGrid">
              <button
                type="button"
                className="compactActionButton scan"
                onClick={startBarcodeScanner}
                disabled={barcodeLoading || scannerStarting}
              >
                <span aria-hidden="true">📷</span>
                <strong>{scannerStarting ? "Starting…" : "Scan Camera"}</strong>
                <small>Point your phone at one barcode</small>
              </button>

              <label className="compactActionButton upload">
                <span aria-hidden="true">🖼️</span>
                <strong>Upload Photo</strong>
                <small>Choose a saved barcode picture</small>
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={scanBarcodePhoto}
                />
              </label>

              <button
                type="button"
                className="compactActionButton manual"
                onClick={() => setProductTool(productTool === "manual" ? "" : "manual")}
              >
                <span aria-hidden="true">⌨️</span>
                <strong>Enter UPC</strong>
                <small>Search or type item details</small>
              </button>
            </div>

            {(productTool || form.item_name || form.barcode) && (
              <div className="compactProductWorkspace">
                <div className="compactLookupRow">
                  <div>
                    <strong>Product lookup</strong>
                    <span>Scan or enter the UPC below.</span>
                  </div>
                  <form onSubmit={lookupBarcode}>
                    <input
                      inputMode="numeric"
                      autoComplete="off"
                      value={barcodeSearch}
                      onChange={(e) => setBarcodeSearch(e.target.value.replace(/\s/g, ""))}
                      placeholder="UPC or EAN number"
                    />
                    <button type="submit" disabled={barcodeLoading}>
                      {barcodeLoading ? "Searching…" : "Search"}
                    </button>
                  </form>
                </div>

                <form className="compactItemForm" onSubmit={addItem}>
                  <label className="compactField wide">
                    <span>Item name</span>
                    <input
                      placeholder="Example: chicken breast"
                      value={form.item_name}
                      onChange={(e) => change("item_name", e.target.value)}
                      required
                    />
                  </label>

                  <label className="compactField">
                    <span>Quantity</span>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      value={form.quantity}
                      onChange={(e) => change("quantity", e.target.value)}
                      required
                    />
                  </label>

                  <label className="compactField">
                    <span>Category</span>
                    <select value={form.category} onChange={(e) => change("category", e.target.value)}>
                      {CATEGORY_OPTIONS.map((category) => <option key={category}>{category}</option>)}
                    </select>
                  </label>

                  <label className="compactField">
                    <span>Unit</span>
                    <select value={form.unit} onChange={(e) => change("unit", e.target.value)}>
                      {UNIT_OPTIONS.map((unit) => <option key={unit}>{unit}</option>)}
                    </select>
                  </label>

                  <label className="compactField">
                    <span>Expiration date</span>
                    <input
                      type="date"
                      value={form.expiration_date}
                      onChange={(e) => change("expiration_date", e.target.value)}
                    />
                  </label>

                  <label className="compactField">
                    <span>Container</span>
                    <select
                      value={form.container_type}
                      onChange={(e) => change("container_type", e.target.value)}
                    >
                      <option value="">Select container</option>
                      {CONTAINER_OPTIONS.filter(Boolean).map((container) => (
                        <option key={container}>{container}</option>
                      ))}
                    </select>
                  </label>

                  <label className="compactField">
                    <span>Brand</span>
                    <input
                      placeholder="Optional"
                      value={form.brand}
                      onChange={(e) => change("brand", e.target.value)}
                    />
                  </label>

                  <label className="compactField">
                    <span>Barcode / UPC</span>
                    <input
                      placeholder="Optional"
                      value={form.barcode}
                      onChange={(e) => change("barcode", e.target.value)}
                    />
                  </label>

                  <label className="compactField wide">
                    <span>Notes</span>
                    <input
                      placeholder="Optional: opened, frozen, or half-full"
                      value={form.notes}
                      onChange={(e) => change("notes", e.target.value)}
                    />
                  </label>

                  <div className="compactFormActions wide">
                    <button type="button" className="compactCancelButton" onClick={() => setProductTool("")}>
                      Collapse
                    </button>
                    <button type="submit" className="compactSaveButton">
                      Add item to pantry
                    </button>
                  </div>
                </form>
              </div>
            )}
          </>
        ) : (
          <div className="compactReceiptWorkspace">
            <div className="compactActionGrid receiptActions">
              <button
                type="button"
                className="compactActionButton scan"
                onClick={startReceiptCamera}
                disabled={receiptCameraStarting}
              >
                <span aria-hidden="true">📷</span>
                <strong>{receiptCameraStarting ? "Starting…" : "Take Photo"}</strong>
                <small>Open the camera and capture the receipt</small>
              </button>

              <label className="compactActionButton upload">
                <span aria-hidden="true">🖼️</span>
                <strong>Upload Image</strong>
                <small>Choose a saved receipt photo</small>
                <input type="file" accept="image/*" onChange={handleReceiptFile} />
              </label>

              <label className="compactActionButton file">
                <span aria-hidden="true">📄</span>
                <strong>Upload File</strong>
                <small>TXT or CSV grocery list</small>
                <input type="file" accept=".txt,.csv,text/csv" onChange={handleGroceryTextFile} />
              </label>
            </div>

            {(receiptFile || receiptPreview || ocrText || detectedItems.length > 0) && (
              <div className="compactReceiptDetails">
                <div className="compactReceiptToolbar">
                  <div>
                    <strong>Import / receipt review</strong>
                    <span>Scan, correct, and choose the items you want to save.</span>
                  </div>
                  <div>
                    <button type="button" onClick={clearReceiptScan}>Clear</button>
                    <button type="button" onClick={scanReceiptWithOcr} disabled={ocrLoading}>
                      {ocrLoading ? `Scanning ${ocrProgress}%` : "Scan with OCR"}
                    </button>
                  </div>
                </div>

                {receiptPreview && (
                  <div className="compactReceiptPreview">
                    <img src={receiptPreview} alt="Uploaded receipt preview" />
                    <div>
                      <strong>Make the receipt easy to read</strong>
                      <span>Lay it flat, avoid shadows, and keep the full receipt in frame.</span>
                      <div className="ocrProgressBar"><span style={{ width: `${ocrProgress}%` }} /></div>
                    </div>
                  </div>
                )}

                <textarea
                  className="compactReceiptText"
                  value={ocrText}
                  onChange={(e) => setOcrText(e.target.value)}
                  placeholder={"Scanned text appears here. You can also paste grocery lines."}
                />

                <div className="compactReceiptTextActions">
                  <button type="button" onClick={detectItemsFromText}>Detect items</button>
                  <button type="button" onClick={useOcrLinesAsItems}>Move lines to review</button>
                </div>

                {detectedItems.length > 0 && (
                  <div className="compactDetectedItems">
                    <div className="compactDetectedHeader">
                      <strong>{detectedItems.length} possible item(s)</strong>
                      <span>{detectedItems.filter((item) => item.selected).length} selected</span>
                    </div>

                    <div className="compactDetectedList">
                      {detectedItems.map((item, index) => (
                        <article key={`${item.item_name}-${index}`}>
                          <input
                            type="checkbox"
                            checked={item.selected}
                            onChange={(e) => changeDetected(index, "selected", e.target.checked)}
                            aria-label={`Add ${item.item_name || `item ${index + 1}`}`}
                          />
                          <input
                            value={item.item_name}
                            onChange={(e) => changeDetected(index, "item_name", e.target.value)}
                            placeholder="Item name"
                          />
                          <input
                            type="number"
                            min="0"
                            step="0.1"
                            value={item.quantity}
                            onChange={(e) => changeDetected(index, "quantity", e.target.value)}
                            aria-label="Quantity"
                          />
                          <select
                            value={item.unit}
                            onChange={(e) => changeDetected(index, "unit", e.target.value)}
                          >
                            {UNIT_OPTIONS.map((unit) => <option key={unit}>{unit}</option>)}
                          </select>
                          <input
                            type="date"
                            value={item.expiration_date}
                            onChange={(e) => changeDetected(index, "expiration_date", e.target.value)}
                          />
                        </article>
                      ))}
                    </div>

                    <button className="compactSaveButton fullWidth" onClick={addDetectedItems}>
                      Add selected items to pantry
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        <div className="compactQuickTip">
          <span aria-hidden="true">💡</span>
          <strong>Barcode = one item</strong>
          <strong>Receipt = many items</strong>
        </div>

        {message && <p className="success compactNotice" role="status">{message}</p>}
        {error && <p className="error compactNotice" role="alert">{error}</p>}
        </section>

        <aside className="compactPantrySidePanel">
          <div className="sidePanelIcon" aria-hidden="true">💡</div>
          <div>
            <p className="eyebrow">Quick tip</p>
            <h3>Make pantry updates easy</h3>
            <p>
              Add items while unpacking groceries so your pantry stays ready for better meal ideas.
            </p>
          </div>

          <div className="sidePanelDivider" />

          <div>
            <p className="eyebrow">Need ideas?</p>
            <h3>Cook with what you have</h3>
            <p>
              Find meals that use your pantry items and prioritize foods that expire soon.
            </p>
          </div>

          <a href="/recommendations" className="sidePanelFindMeals">
            Find Meals
          </a>
        </aside>
      </div>

      {scannerOpen && (
        <div className="barcodeScannerOverlay" role="dialog" aria-modal="true" aria-labelledby="barcode-scanner-title">
          <div className="barcodeScannerModal">
            <div className="barcodeScannerHeader">
              <div>
                <p className="eyebrow">Camera barcode scanner</p>
                <h2 id="barcode-scanner-title">Scan product barcode</h2>
              </div>
              <button type="button" onClick={closeBarcodeScanner} aria-label="Close barcode scanner">×</button>
            </div>
            <div className="barcodeVideoFrame">
              <video ref={scannerVideoRef} muted playsInline autoPlay />
              <div className="barcodeTargetBox" aria-hidden="true" />
            </div>
            <p className="barcodeScannerStatus">{scannerMessage || "Starting the camera…"}</p>
            <button type="button" className="barcodeCancelButton" onClick={closeBarcodeScanner}>
              Cancel scan
            </button>
          </div>
        </div>
      )}


      {receiptCameraOpen && (
        <div className="receiptCameraOverlay" role="dialog" aria-modal="true" aria-labelledby="receipt-camera-title">
          <div className="receiptCameraModal">
            <div className="receiptCameraHeader">
              <div>
                <p className="eyebrow">Grocery receipt camera</p>
                <h2 id="receipt-camera-title">Take receipt photo</h2>
              </div>
              <button type="button" onClick={closeReceiptCamera} aria-label="Close receipt camera">×</button>
            </div>

            <div className="receiptVideoFrame">
              <video ref={receiptVideoRef} muted playsInline autoPlay />
              <div className="receiptCaptureGuide" aria-hidden="true" />
            </div>

            <p className="receiptCameraStatus">
              {receiptCameraMessage || "Starting the camera…"}
            </p>

            <div className="receiptCameraActions">
              <button type="button" className="receiptCameraCancel" onClick={closeReceiptCamera}>
                Cancel
              </button>
              <button
                type="button"
                className="receiptCameraCapture"
                onClick={captureReceiptPhoto}
                disabled={receiptCameraStarting}
              >
                {receiptCameraStarting ? "Starting camera…" : "Capture receipt"}
              </button>
            </div>
          </div>
        </div>
      )}

      <section className="card compactPantryListCard">
        <div className="compactPantryListHeader">
          <div>
            <p className="eyebrow">Current pantry</p>
            <h2>Your saved items</h2>
          </div>
          <span>{filteredPantryItems.length} shown</span>
        </div>

        <div className="compactPantryFilters">
          <label className="pantrySearchField">
            <span aria-hidden="true">⌕</span>
            <input
              value={pantrySearch}
              onChange={(e) => setPantrySearch(e.target.value)}
              placeholder="Search items or brands"
            />
          </label>

          <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            <option value="all">All categories</option>
            {categoryOptionsForFilter.map((category) => (
              <option key={category}>{category}</option>
            ))}
          </select>

          <button
            type="button"
            className={useSoonOnly ? "active" : ""}
            onClick={() => setUseSoonOnly((current) => !current)}
          >
            ◷ Use soon
          </button>
        </div>

        {loading ? (
          <div className="compactEmptyState">Loading pantry items…</div>
        ) : filteredPantryItems.length === 0 ? (
          <div className="compactEmptyState">
            <strong>No matching pantry items.</strong>
            <span>Try another search or add an item above.</span>
          </div>
        ) : (
          <>
            <div className="compactDesktopTableWrap">
              <table className="compactPantryTable">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>Category</th>
                    <th>Quantity</th>
                    <th>Expires</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPantryItems.map((item) => {
                    const rowIndex = editedItems.findIndex((row) => row.id === item.id);
                    const status = pantryStatus(item);
                    return (
                      <tr key={item.id}>
                        <td>
                          <div className="desktopPantryItemName">
                            <span className="desktopFoodIcon" aria-hidden="true">
                              {categoryIcon(item.category)}
                            </span>
                            <div>
                              <input
                                value={item.item_name}
                                onChange={(e) => changeTable(rowIndex, "item_name", e.target.value)}
                              />
                              <small>{item.brand || item.container_type || "Pantry item"}</small>
                            </div>
                          </div>
                        </td>
                        <td>
                          <select
                            value={item.category}
                            onChange={(e) => changeTable(rowIndex, "category", e.target.value)}
                          >
                            {CATEGORY_OPTIONS.map((category) => <option key={category}>{category}</option>)}
                          </select>
                        </td>
                        <td>
                          <div className="quantityCell">
                            <input
                              type="number"
                              min="0"
                              step="0.1"
                              value={item.quantity}
                              onChange={(e) => changeTable(rowIndex, "quantity", e.target.value)}
                            />
                            <select
                              value={item.unit}
                              onChange={(e) => changeTable(rowIndex, "unit", e.target.value)}
                            >
                              {UNIT_OPTIONS.map((unit) => <option key={unit}>{unit}</option>)}
                            </select>
                          </div>
                        </td>
                        <td>
                          <input
                            type="date"
                            value={item.expiration_date}
                            onChange={(e) => changeTable(rowIndex, "expiration_date", e.target.value)}
                          />
                        </td>
                        <td>
                          <span className={`pantryStatus ${status.className}`}>{status.label}</span>
                        </td>
                        <td>
                          <div className="compactRowActions">
                            <button type="button" onClick={() => saveRow(item)}>Save</button>
                            <button type="button" onClick={() => resetRow(rowIndex)}>Reset</button>
                            <button type="button" className="delete" onClick={() => remove(item.id)}>Delete</button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="compactMobilePantryList">
              {filteredPantryItems.map((item) => {
                const rowIndex = editedItems.findIndex((row) => row.id === item.id);
                const status = pantryStatus(item);
                return (
                  <article key={item.id}>
                    <div className="mobilePantryItemMain">
                      <span className="mobileFoodIcon" aria-hidden="true">{categoryIcon(item.category)}</span>
                      <div>
                        <strong>{item.item_name}</strong>
                        <small>{item.quantity} {item.unit} · {item.category}</small>
                      </div>
                    </div>
                    <span className={`pantryStatus ${status.className}`}>{status.label}</span>
                    <div className="mobilePantryActions">
                      <button type="button" onClick={() => saveRow(item)}>Save</button>
                      <button type="button" onClick={() => resetRow(rowIndex)}>Reset</button>
                      <button type="button" className="delete" onClick={() => remove(item.id)}>Delete</button>
                    </div>
                  </article>
                );
              })}
            </div>
          </>
        )}

        <button
          type="button"
          className="addAnotherItemButton"
          onClick={() => {
            setEntryMode("product");
            setProductTool("manual");
            window.scrollTo({ top: 0, behavior: "smooth" });
          }}
        >
          + Add another item
        </button>
      </section>

    </div>
  );
}
